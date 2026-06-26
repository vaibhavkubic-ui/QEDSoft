from pathlib import Path
import shutil
import unittest

from qedsoft.models import ProjectConfig
from qedsoft.orchestrator import QEDSoft


class QEDSoftSmokeTest(unittest.TestCase):
    def test_fifo_static_flow(self) -> None:
        root = Path(__file__).resolve().parents[1]
        spec = root / "examples" / "fifo" / "spec.md"
        rtl = root / "examples" / "fifo" / "fifo.sv"
        output_dir = root / "runs" / "_test" / "fifo"
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        result = QEDSoft(ProjectConfig(use_external_tools=False)).run_from_paths(
            spec_path=spec,
            rtl_path=rtl,
            output_dir=output_dir,
        )
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.formalization.subgoals), 3)
        self.assertTrue(any(artifact.kind == "sva" for artifact in result.artifacts))
        self.assertTrue(any(artifact.kind == "lean" for artifact in result.artifacts))
        shutil.rmtree(root / "runs" / "_test", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
