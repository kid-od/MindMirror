import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentPromptCoverageTest(unittest.TestCase):
    def test_agent_prompt_requires_search_for_specific_uploaded_essay_requests(self):
        source = (ROOT / "backend" / "agent.py").read_text(encoding="utf-8")

        self.assertIn("specific uploaded essay", source)
        self.assertIn("must call search_knowledge_base", source)


if __name__ == "__main__":
    unittest.main()
