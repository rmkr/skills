export const meta = {
  name: 'forge',
  description: 'The Forge loop: independent review, verify every finding, fix, and re-review until clean',
  whenToUse: 'Started by the forge skill when the user attaches workflow; args come from the skill',
  phases: [
    { title: 'Snapshot', detail: 'capture the target and its fingerprint' },
    { title: 'Review', detail: 'fresh adversarial reviewer each round' },
    { title: 'Verify', detail: 'one verifier per finding' },
    { title: 'Complexity', detail: 'one cut pass after the first clean review' },
    { title: 'Fix', detail: 'apply accepted findings and run checks' },
  ],
}

const LEVELS = ['review', 'fix']
if (!args || !LEVELS.includes(args.level)) throw new Error(`args.level must be one of ${LEVELS.join(', ')}`)
for (const key of ['brief', 'target', 'snapshot']) {
  if (typeof args[key] !== 'string' || !args[key].trim()) throw new Error(`args.${key} is required`)
}
const checks = args.checks || []
const models = args.models || {}
const maxRounds = args.max_rounds || Infinity
const tiers = args.tiers || []
if (args.dynamic && !tiers.length) throw new Error('args.tiers is required with args.dynamic')
const tierNames = tiers.map(t => t.name)

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
        },
        required: ['kind', 'severity', 'ref', 'trigger', 'impact', 'correction', 'repeats'],
      },
    },
    open_questions: { type: 'array', items: { type: 'string' } },
    coverage_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'open_questions', 'coverage_gaps'],
}
const VERDICT = {
  type: 'object',
  properties: {
    disposition: { type: 'string', enum: ['accepted', 'rejected', 'unresolved'] },
    reason: { type: 'string' },
  },
  required: ['disposition', 'reason'],
}
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

if (args.dynamic) {
  FINDINGS.properties.findings.items.properties.tier = { type: 'string', enum: tierNames }
  FINDINGS.properties.findings.items.required.push('tier')
}
// Delegation's escalation rule: one tier up after a failed fix, from engineer only after two.
const tierIndex = (name, failures = 0) => {
  const i = Math.max(0, tierNames.indexOf(name))
  return Math.min(i + (failures >= (name === 'engineer' ? 2 : 1) ? 1 : 0), tiers.length - 1)
}
const tierOpts = i => ({ ...(tiers[i].model && { model: tiers[i].model }), ...(tiers[i].effort && { effort: tiers[i].effort }) })
const tierGuide = args.dynamic
  ? `\n\nSet each finding's \`tier\` to the lowest tier that can verify and fix it well. Tiers, lowest first:\n` +
    tiers.map(t => `- ${t.name}: ${t.work || ''}`).join('\n')
  : ''

const opts = (role, phase, extra = {}, tier = null) => ({ ...(tier || models[role]), phase, ...extra })
const context = `## Brief\n${args.brief}\n\n## Target\n${args.target}`
const line = f => `${f.id} [${f.kind}/${f.severity}${f.tier ? `/${f.tier}` : ''}] ${f.ref}: ${f.trigger} -> ${f.correction}` +
  (f.disposition ? ` (${f.disposition}: ${f.reason})` : '')

async function snapshot(label) {
  const result = await agent(
    `Run this command from the target checkout and return its exact stdout, trimmed, as the fingerprint. ` +
    `Change nothing else.\n\n${args.snapshot}`,
    opts('snapshot', 'Snapshot', { label, schema: SNAPSHOT }, args.dynamic ? tierOpts(0) : null),
  )
  return result && result.fingerprint
}

function verify(found) {
  return parallel(found.map(f => async () => {
    const verdict = await agent(
      `${context}\n\n## Finding ${f.id}\n${JSON.stringify(f, null, 2)}\n\n` +
      'Verify this finding against the target and the brief. Inspect only: leave the target unchanged, and run any ' +
      'check that writes files in an isolated copy. Use the smallest check that settles the claim. Accept it only ' +
      'with evidence. Reject unsupported, speculative, or preference-only claims. Mark it unresolved when settling ' +
      "it needs missing information, extra authority, or a change to the user's goal or intended position.",
      opts('verifier', 'Verify', { label: `verify:${f.id}`, schema: VERDICT }, args.dynamic ? tierOpts(tierIndex(f.tier)) : null),
    )
    return { ...f, ...(verdict || { disposition: 'unresolved', reason: 'verifier failed' }) }
  }))
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

while (!status) {
  round++
  if (round > maxRounds) { status = 'budget'; break }

  fingerprint = await snapshot(`snapshot:${round}`)
  if (!fingerprint) { status = 'snapshot-failed'; break }

  const prior = ledger.length
    ? `\n\n## Earlier findings\nCheck every accepted finding against the current state, including accepted ` +
      `complexity cuts against the brief and the accepted fixes. Raise a rejected finding again only with new ` +
      `evidence. Set \`repeats\` to the earlier ID when a finding repeats one.\n${ledger.map(line).join('\n')}`
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
    opts('reviewer', 'Review', {
      label: `review:${round}`,
      schema: FINDINGS,
      ...(args.strict ? { agentType: 'forge-strict-reviewer' } : {}),
    }),
  )
  if (!review) { status = 'reviewer-failed'; break }
  review.open_questions.forEach(q => questions.add(q))
  review.coverage_gaps.forEach(g => gaps.add(g))

  let found = await verify(review.findings.map((f, i) => ({ ...f, id: `R${round}-${i + 1}`, round })))
  ledger.push(...found)

  if (!found.some(f => f.disposition === 'accepted') && !complexityDone && args.level === 'fix') {
    complexityDone = true
    const cuts = await agent(
      `${context}\n\nApply the ponytail-review skill (plugin installs name it ponytail:ponytail-review) to the ` +
      `combined target once. Report each cut as a finding with kind "complexity". Inspect only.${tierGuide}`,
      opts('complexity', 'Complexity', { label: `complexity:${round}`, schema: FINDINGS }),
    )
    if (cuts) {
      const verified = await verify(cuts.findings.map((f, i) => ({ ...f, kind: 'complexity', id: `C${round}-${i + 1}`, round })))
      ledger.push(...verified)
      found = found.concat(verified)
    }
  }

  if ((await snapshot(`recheck:${round}`)) !== fingerprint) { status = 'changed'; break }

  const accepted = found.filter(f => f.disposition === 'accepted')
  const unresolved = found.filter(f => f.disposition === 'unresolved')
  if (args.level === 'review') { status = accepted.length || unresolved.length ? 'findings' : 'clean'; break }
  if (!accepted.length) {
    if (unresolved.length) status = 'unresolved'
    else if (lastFix && lastFix.checks.some(c => !c.passed)) status = 'checks-failed'
    else status = 'clean'
    break
  }

  // The same issue surviving two fixes needs diagnosis, not a third attempt.
  accepted.forEach(f => { sightings[root(f)] = (sightings[root(f)] || 0) + 1 })
  if (accepted.some(f => sightings[root(f)] >= 3)) { status = 'stalled'; break }

  let fixTier = null
  if (args.dynamic) {
    const planned = Math.max(...accepted.map(f => tierIndex(f.tier)))
    const chosen = Math.max(...accepted.map(f => tierIndex(f.tier, sightings[root(f)] - 1)))
    if (chosen > planned) escalations.push(`round ${round}: fixer ${tierNames[planned]} -> ${tierNames[chosen]}`)
    fixTier = tierOpts(chosen)
  }
  lastFix = await agent(
    `${context}\n\n## Accepted findings\n${accepted.map(line).join('\n')}\n\n` +
    'Apply the smallest correction for each accepted finding in the target checkout. Stay within the brief, preserve ' +
    'unrelated and pre-existing changes, and leave committing to the orchestrator. Then run each check and report it' +
    (checks.length ? `:\n${checks.map(c => `- ${c}`).join('\n')}` : '; there are none, so return an empty list.'),
    opts('fixer', 'Fix', { label: `fix:${round}`, schema: FIX }, fixTier),
  )
  if (!lastFix) { status = 'fixer-failed'; break }
  log(`round ${round}: fixed ${accepted.length} finding(s)`)
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
