import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentPromptCoverageTest(unittest.TestCase):
    def test_agent_prompt_requires_search_for_specific_uploaded_essay_requests(self):
        source = (ROOT / "backend" / "agent.py").read_text(encoding="utf-8")

        self.assertIn("specific uploaded essay", source)
        self.assertIn("must call search_knowledge_base", source)
        self.assertIn("EXACT_ESSAY_MATCH_FOUND", source)
        self.assertIn("must treat that essay as found", source)

    def test_agent_prompt_biases_toward_warm_friend_like_reflection(self):
        source = (ROOT / "backend" / "agent.py").read_text(encoding="utf-8")

        self.assertIn("thoughtful, trustworthy friend", source)
        self.assertIn("briefly acknowledge the user's feeling", source)
        self.assertIn("Avoid sounding clinical, robotic, preachy, or overly formal", source)
        self.assertIn("Do not sound like a therapist writing an assessment report", source)
        self.assertIn("use it as the primary basis of the analysis", source)

    def test_agent_model_temperature_is_raised_for_more_human_responses(self):
        source = (ROOT / "backend" / "agent.py").read_text(encoding="utf-8")

        self.assertIn("temperature=0.6", source)


if __name__ == "__main__":
    unittest.main()
