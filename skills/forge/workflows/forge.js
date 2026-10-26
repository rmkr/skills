export const meta = {
  name: 'forge',
  description: 'The Forge loop: independent review, verify every finding, fix, and re-review until clean',
  whenToUse: 'Started by the forge skill when the user attaches workflow; args come from the skill',
  phases: [
    { title: 'Snapshot', detail: 'capture the target and its fingerprint' },
    { title: 'Review', detail: 'fresh adversarial reviewer each round' },
    { title: 'Verify', detail: 'group related findings at the same tier' },
    { title: 'Complexity', detail: 'one cut pass after the first clean review' },
    { title: 'Fix', detail: 'apply accepted findings and run checks' },
  ],
}

const LEVELS = ['review', 'fix']
if (!args || !LEVELS.includes(args.level)) throw new Error(`args.level must be one of ${LEVELS.join(', ')}`)
for (const key of ['brief', 'target', 'snapshot']) {
  if (typeof args[key] !== 'string' || !args[key].trim()) throw new Error(`args.${key} is required`)
}
const tiers = args.tiers || []
const tierNames = tiers.map(t => t.name)
for (const name of ['apprentice', 'engineer']) {
  if (!tierNames.includes(name)) throw new Error(`args.tiers must list ${name}`)
}
const checks = args.checks || []
const maxRounds = args.max_rounds || Infinity
// Below this, skip starting another round.
const ROUND_RESERVE = 20000

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          kind: { type: 'string', enum: ['premise', 'delivery', 'complexity'] },
          severity: { type: 'string', enum: ['blocking', 'major', 'minor'] },
          ref: { type: 'string', description: 'Tight file:line or artifact location' },
          trigger: { type: 'string' },
          impact: { type: 'string' },
          correction: { type: 'string', description: 'Smallest defensible correction' },
          repeats: { type: 'string', description: 'ID of the earlier finding this one repeats, or empty' },
          tier: { type: 'string', enum: tierNames },
          verification_group: { type: 'string', description: 'Shared key for findings needing the same source context; empty keeps a finding separate' },
        },
        required: ['kind', 'severity', 'ref', 'trigger', 'impact', 'correction', 'repeats', 'tier', 'verification_group'],
      },
    },
    open_questions: { type: 'array', items: { type: 'string' } },
    coverage_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'open_questions', 'coverage_gaps'],
}
const verdictSchema = found => ({
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', enum: found.map(f => f.id) },
          disposition: { type: 'string', enum: ['accepted', 'rejected', 'unresolved'] },
          reason: { type: 'string' },
        },
        required: ['id', 'disposition', 'reason'],
      },
    },
  },
  required: ['verdicts'],
})
const SNAPSHOT = {
  type: 'object',
  properties: { fingerprint: { type: 'string' } },
  required: ['fingerprint'],
}
const FIX = {
  type: 'object',
  properties: {
    changed: { type: 'array', items: { type: 'string' } },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: { command: { type: 'string' }, passed: { type: 'boolean' }, output: { type: 'string' } },
        required: ['command', 'passed', 'output'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['changed', 'checks', 'notes'],
}

// One tier up after a failed fix. Engineer would need two failures, but the stall rule stops first.
const tierIndex = (name, failures = 0) => {
  const i = tierNames.includes(name) ? tierNames.indexOf(name) : tierNames.indexOf('engineer')
  return Math.min(i + (failures >= 1 && tierNames[i] !== 'engineer' ? 1 : 0), tiers.length - 1)
}
const effortOf = e => (e === 'ultra' ? 'max' : e)
const modelOpts = ({ model, effort } = {}) => ({ ...(model && { model }), ...(effort && { effort: effortOf(effort) }) })
const tierOpts = i => modelOpts(tiers[i])
const reviewerOpts = args.strict ? modelOpts({ model: (args.reviewer || {}).model }) : modelOpts(args.reviewer)
const tierGuide = `\n\nSet each finding's \`tier\` to the lowest tier that can verify and fix it well. Tiers, lowest first:\n` +
  tiers.map(t => `- ${t.name}: ${t.work || ''}`).join('\n')

const context = `## Brief\n${args.brief}\n\n## Target\n${args.target}`
const line = f => `${f.id} [${f.kind}/${f.severity}${f.tier ? `/${f.tier}` : ''}] ${f.ref}: ${f.trigger} -> ${f.correction}` +
  (f.disposition ? ` (${f.disposition}: ${f.reason})` : '')

async function snapshot(label) {
  const result = await agent(
    `Run this command from the target checkout and return its exact stdout, trimmed, as the fingerprint. ` +
    `Change nothing else.\n\n${args.snapshot}`,
    { ...tierOpts(tierIndex('apprentice')), phase: 'Snapshot', label, schema: SNAPSHOT },
  )
  return result && result.fingerprint
}

async function verify(found) {
  const groups = new Map()
  for (const f of found) {
    const shared = typeof f.verification_group === 'string' && f.verification_group.trim()
    const key = JSON.stringify([tierIndex(f.tier), shared ? ['group', shared] : ['finding', f.id]])
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(f)
  }
  const batches = [...groups.values()]
  const results = await parallel(batches.map(batch => () => agent(
    `${context}\n\n## Findings\n${JSON.stringify(batch, null, 2)}\n\n` +
    'Verify each finding against the target and the brief. Share inspection across related findings, but return ' +
    'one verdict with its original id and evidence for each finding. Inspect only: leave the target unchanged, ' +
    'and run any check that writes files in an isolated copy. Use the smallest check that settles each claim. ' +
    'Accept only with evidence. Reject unsupported, speculative, or preference-only claims. Mark a finding ' +
    "unresolved when settling it needs missing information, extra authority, or a change to the user's goal or intended position.",
    { ...tierOpts(tierIndex(batch[0].tier)), phase: 'Verify', label: `verify:${batch[0].id}`, schema: verdictSchema(batch) },
  )))
  const checked = new Map()
  batches.forEach((batch, i) => {
    const verdicts = results[i] && results[i].verdicts
    for (const f of batch) {
      const matches = Array.isArray(verdicts) ? verdicts.filter(v => v && v.id === f.id) : []
      const v = matches.length === 1 && matches[0]
      checked.set(f.id, v && ['accepted', 'rejected', 'unresolved'].includes(v.disposition) &&
        typeof v.reason === 'string' && v.reason.trim()
        ? { ...f, disposition: v.disposition, reason: v.reason }
        : { ...f, disposition: 'unresolved', reason: 'verifier failed or returned a missing, duplicate, or invalid verdict' })
    }
  })
  return found.map(f => checked.get(f.id))
}

const ledger = []
const questions = new Set()
const gaps = new Set()
const sightings = {}
const escalations = []
const root = f => (f.repeats && ledger.find(e => e.id === f.repeats) ? root(ledger.find(e => e.id === f.repeats)) : f.id)

let round = 0
let lastFix = null
let complexityDone = !args.complexity || args.strict
let status = null
let fingerprint = null

// A spent budget makes agent() throw mid-round; end with `budget` so the ledger still comes back.
while (!status) try {
  round++
  if (round > maxRounds || (budget.total && budget.remaining() < ROUND_RESERVE)) { status = 'budget'; break }

  fingerprint = await snapshot(`snapshot:${round}`)
  if (!fingerprint) { status = 'snapshot-failed'; break }
  const unchanged = async label => {
    const now = await snapshot(label)
    if (!now) status = 'snapshot-failed'
    else if (now !== fingerprint) status = 'changed'
    return !status
  }

  const prior = ledger.length
    ? `\n\n## Earlier findings\nCheck every accepted and unresolved finding against the current state, including ` +
      `accepted complexity cuts against the brief and the accepted fixes. Raise a rejected finding again only with ` +
      `new evidence. Set \`repeats\` to the earlier ID when a finding repeats one.\n${ledger.map(line).join('\n')}`
    : ''
  const evidence = lastFix
    ? `\n\n## Last fix\nChanged: ${lastFix.changed.join(', ') || 'nothing'}\n${lastFix.notes}\n` +
      lastFix.checks.map(c => `- ${c.command}: ${c.passed ? 'passed' : 'FAILED'}\n${c.output}`).join('\n')
    : ''
  const review = await agent(
    `${context}${prior}${evidence}\n\n` +
    'Review the target adversarially and independently. Inspect only. Challenge the underlying goal and assumptions ' +
    '(premise) and fulfillment of the agreed brief (delivery). You may challenge the criteria with evidence. Ground ' +
    'each finding in the brief, evidence, constraints, or concrete audience needs, with a concrete counterexample ' +
    'where useful. Keep unsupported taste and speculative hardening out of the findings. Put open questions and ' +
    `coverage gaps in their own lists. Return an empty findings list when no defect meets that bar.${tierGuide}`,
    {
      ...reviewerOpts,
      phase: 'Review',
      label: `review:${round}`,
      schema: FINDINGS,
      ...(args.strict ? { agentType: 'forge-strict-reviewer' } : {}),
    },
  )
  if (!review) { status = 'reviewer-failed'; break }
  review.open_questions.forEach(q => questions.add(q))
  review.coverage_gaps.forEach(g => gaps.add(g))
  const raised = review.findings.map((f, i) => ({ ...f, id: `R${round}-${i + 1}`, round }))
  if (args.strict && !(await unchanged(`after-review:${round}`))) {
    ledger.push(...raised.map(f => ({ ...f, disposition: 'unresolved', reason: `unverified: reviewed bundle ${fingerprint}` })))
    break
  }

  let found = await verify(raised)
  ledger.push(...found)

  if (!found.some(f => f.disposition === 'accepted') && !complexityDone) {
    complexityDone = true
    const cuts = await agent(
      `${context}\n\nApply the ponytail-review skill (plugin installs name it ponytail:ponytail-review) to the ` +
      `combined target once. Report each cut as a finding with kind "complexity". Inspect only.${tierGuide}`,
      { ...tierOpts(tierIndex('engineer')), phase: 'Complexity', label: `complexity:${round}`, schema: FINDINGS },
    )
    if (cuts) {
      const verified = await verify(cuts.findings.map((f, i) => ({ ...f, kind: 'complexity', id: `C${round}-${i + 1}`, round })))
      ledger.push(...verified)
      found = found.concat(verified)
    }
  }

  if (!(await unchanged(`recheck:${round}`))) break

  const accepted = found.filter(f => f.disposition === 'accepted')
  // Unresolved findings from any round block a clean result until a later repeat settles them.
  const unresolved = ledger.some(f => f.disposition === 'unresolved' &&
    !ledger.some(g => g.round > f.round && root(g) === root(f) && g.disposition !== 'unresolved'))
  if (args.level === 'review') { status = accepted.length || unresolved ? 'findings' : 'clean'; break }
  if (!accepted.length) {
    if (unresolved) status = 'unresolved'
    else if (lastFix && lastFix.checks.some(c => !c.passed)) status = 'checks-failed'
    else status = 'clean'
    break
  }

  // The same issue surviving two fixes needs diagnosis, not a third attempt.
  new Set(accepted.map(root)).forEach(r => { sightings[r] = (sightings[r] || 0) + 1 })
  if (accepted.some(f => sightings[root(f)] >= 3)) { status = 'stalled'; break }

  const planned = Math.max(...accepted.map(f => tierIndex(f.tier)))
  const chosen = Math.max(...accepted.map(f => tierIndex(f.tier, sightings[root(f)] - 1)))
  if (chosen > planned) escalations.push(`round ${round}: fixer ${tierNames[planned]} -> ${tierNames[chosen]}`)
  lastFix = await agent(
    `${context}\n\n## Accepted findings\n${accepted.map(line).join('\n')}\n\n` +
    'Apply the smallest correction for each accepted finding in the target checkout. Stay within the brief, preserve ' +
    'unrelated and pre-existing changes, and leave committing to the orchestrator. Then run each check and report it' +
    (checks.length ? `:\n${checks.map(c => `- ${c}`).join('\n')}` : '; there are none, so return an empty list.'),
    { ...tierOpts(chosen), phase: 'Fix', label: `fix:${round}`, schema: FIX },
  )
  if (!lastFix) { status = 'fixer-failed'; break }
  log(`round ${round}: fixed ${accepted.length} finding(s)`)
} catch (error) {
  if (!(budget.total && budget.remaining() <= 0)) throw error
  status = 'budget'
}

return {
  status,
  level: args.level,
  rounds: round,
  fingerprint,
  ledger,
  open_questions: [...questions],
  coverage_gaps: [...gaps],
  escalations,
  last_checks: lastFix ? lastFix.checks : [],
}
