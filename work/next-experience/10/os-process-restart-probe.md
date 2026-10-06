# Bounded OS-process restart probe

Prepared for TASK10; execution belongs exclusively to Tester. This is a controlled Linux test, not live-provider or UI evidence. It creates its own temporary SQLite database, seeds released static demo fixtures, starts the actual FastAPI lifespan in a child OS process, and uses real Pi worker code with synthetic loopback HTTP model/Kev responses. It never reads `.env`, uses inherited credentials, or touches existing services. Only its own newly created process group is killed.

Run from the candidate root with its already installed Python environment (replace the evidence label with a unique candidate label):

    .venv/bin/python work/next-experience/10/run_controlled.py "$PWD" candidate-os-process-restart -s -q "$PWD/work/next-experience/10/test_os_process_restart.py"

The harness must be committed/copied inside that candidate; it derives the candidate root from the controlled runner backend cwd and rejects a harness from another checkout.

Preconditions: Linux, existing backend dependencies, Node on PATH, built runtime/pi/dist matching the candidate. Do not install or rebuild silently. Existing capture records production source hashes before/after plus runtime dist; the test prints its own SHA-256, HTTP request/response transcript, synthetic provider requests, child PIDs, SIGKILL exit evidence and child logs into the capture output. Retain failure output. Source mutation invalidates same-candidate attribution.

Assertions: complete a simulated checkout through public API; admit a genuine running Pi turn and wait until its real worker reaches the deliberately blocked loopback model fixture; SIGKILL that isolated process group; relaunch a different API PID against the same temporary DB; read RUN_INTERRUPTED and durable events through public API; replay the interrupted request without new provider invocation; replay checkout confirmation and obtain the original receipt with exactly one order and empty cart; explicitly admit a new turn and reach a packaging clarification without extra order/cart writes.

Limits: demonstrates one controlled hard-process stop/relaunch with local SQLite, committed checkout persistence/idempotency, interrupted-run recovery and explicit continuation. Does not establish arbitrary power loss, disk corruption, multi-host failover, every crash boundary, background-memory restart recovery, real-provider correctness, live UI behavior or human acceptance. It does not inject former-process rows or mock production business services. Other matrix checks remain separate.
