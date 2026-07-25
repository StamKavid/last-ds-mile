A model that predicts "not fraud" for every single transaction scores 99.83%
accuracy on the Kaggle credit card fraud dataset. It also catches zero fraud.

I built a Claude Code plugin (Last DS Mile) to stop AI agents walking into
traps like that one — no baseline, a metric that lies at 0.17% prevalence, a
validation split that leaks the future into the past. Then I did the thing
most plugin authors skip: I tested whether it actually works. Same task, same
model, plugin on vs. off, three trials each, graded blind.

The honest result: mixed. On the vague "build me a model" ask, the plugin
arm went 8-for-8 vs. the unaided model's steady 6-for-8 — a real, isolated,
reproducible gap on exactly two things: scoring a baseline, stating the lift.
But six other checks showed a gap of *zero* — the base model already does
them unprompted. That's not nothing; that's a signal for what to cut.

On a second prompt, the plugin actually did worse — it correctly caught a
planted false claim ("it's 99.9% accurate, ship it") but then stopped to ask
permission before finishing, two times out of three. The unaided model just
finished the job, five for five, no hesitation.

That's not the result I expected. It's the one I'm publishing, with all
twelve raw transcripts, because a test that couldn't have embarrassed me
wouldn't have told me anything.

Early adopter round is open:
→ 30 seconds: star it
→ 10 minutes: try to break a hard gate
→ an afternoon: run it on something real and tell me exactly where it
  got in your way

Full writeup + every transcript: [Substack link]

github.com/stamkavid/last-ds-mile
