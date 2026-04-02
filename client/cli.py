"""Entry point for the recording client.

Usage:
    python -m client
    python -m client.cli [options]

    --robot-ip       Robot IP address (default: 192.168.149.1)
    --robot-port     Robot server port (default: 8080)
    --dataset        Dataset name (default: turbopi_nav)
    --repo-id        Dataset repo placeholder (default: <HF_DATASET_REPO>)
    --fps            Recording FPS (default: 10)
    --episodes       Number of episodes to record (default: 50)
    --episode-time   Max seconds per episode (default: 30)
    --speed          Initial teleop speed (default: 50)
    --data-dir       Runtime data directory (default: data)
"""
import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser.

    Imports for the recording stack are intentionally deferred until after
    argument parsing so `python -m client --help` works even before optional
    runtime dependencies are installed.
    """
    parser = argparse.ArgumentParser(description="TurboPi VLA Recording Client")
    parser.add_argument("--robot-ip", default="192.168.149.1")
    parser.add_argument("--robot-port", type=int, default=8080)
    parser.add_argument("--dataset", default="turbopi_nav")
    parser.add_argument("--repo-id", default="<HF_DATASET_REPO>")
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--episode-time", type=float, default=30.0)
    parser.add_argument("--speed", type=float, default=50.0)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--tasks", nargs="+", default=None,
                        help="Custom task list (overrides defaults)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    from config import RecordingConfig
    from tasks import TaskManager, DEFAULT_TASKS
    from .recording_session import RecordingSession

    config = RecordingConfig(
        robot_ip=args.robot_ip,
        robot_port=args.robot_port,
        dataset_name=args.dataset,
        repo_id=args.repo_id,
        fps=args.fps,
        num_episodes=args.episodes,
        episode_time_s=args.episode_time,
        teleop_speed=args.speed,
        data_dir=Path(args.data_dir),
    )

    tasks = TaskManager(args.tasks if args.tasks else DEFAULT_TASKS)

    session = RecordingSession(config, tasks)
    session.run()


if __name__ == "__main__":
    main()
