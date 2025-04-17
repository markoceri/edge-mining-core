from apscheduler.schedulers.blocking import BlockingScheduler

from edge_mining.shared.scheduler.port import SchedulerPort
from edge_mining.shared.logging.port import LoggerPort
from edge_mining.application.services.mining_orchestrator import MiningOrchestratorService
from edge_mining.shared.settings.settings import AppSettings

class AutomationScheduler(SchedulerPort):
    def __init__(
        self,
        orchestrator: MiningOrchestratorService,
        logger: LoggerPort,
        settings: AppSettings
    ):
        self.orchestrator = orchestrator
        self.logger = logger
        self.settings = settings
        self.scheduler = BlockingScheduler(timezone="UTC")

    def _run_evaluation_job(self):
        """Wrapper to call the orchestrator's evaluation method."""
        self.logger.info("Scheduler triggered: Running evaluation job.")
        try:
            self.orchestrator.evaluate_and_control_miners()
        except Exception as e:
            self.logger.exception("Error during scheduled evaluation job:")
            # Consider sending a critical notification here

    def start(self):
        """Adds the job and starts the scheduler."""
        interval = self.settings.scheduler_interval_seconds
        self.logger.info(f"Starting scheduler. Evaluation job will run every {interval} seconds.")

        self.scheduler.add_job(
            self._run_evaluation_job,
            'interval',
            seconds=interval,
            id='evaluate_mining_job',
            replace_existing=True
        )

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Scheduler stopped.")
            self.scheduler.shutdown()

    def stop(self):
        self.logger.info("Shutting down scheduler...")
        self.scheduler.shutdown()