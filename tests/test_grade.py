"""Grader checks. Run with:  python -m unittest discover tests"""
import unittest

from formeval import data, grade
from formeval.normalize import norm, same_text


class Normalize(unittest.TestCase):
    def test_punctuation_and_case(self):
        self.assertEqual(norm("Pittsburgh,"), "pittsburgh")
        self.assertEqual(norm("SMOKERS!"), "smokers")
        self.assertEqual(norm("(BIAD #93-13104)"), "biad #93-13104")

    def test_inner_punctuation_kept(self):
        self.assertEqual(norm("32,000"), "32,000")
        self.assertEqual(norm("−3.92"), "-3.92")
        self.assertNotEqual(norm("4.6%"), norm("4.2%"))

    def test_spacing(self):
        self.assertTrue(same_text("D. M. Teng", "D.M. Teng"))


class TextPages(unittest.TestCase):
    truth = {"page_id": "x", "kind": "text", "items": [
        {"id": "a", "text": "smoking", "context_must_include": ["period"], "case_type": []},
        {"id": "b", "text": "92", "case_type": []}]}

    def test_extras_lower_the_score(self):
        out = {"marked": [{"text": "smoking", "context": "the period when smoking was banned"},
                          {"text": "92"}, {"text": "radiation"}]}
        rep = grade.grade_page(self.truth, None, out)
        self.assertEqual((rep["correct"], rep["extras"]), (2, ["radiation"]))
        self.assertAlmostEqual(rep["accuracy"], 2 / 3)

    def test_wrong_occurrence_of_repeated_word(self):
        out = {"marked": [{"text": "smoking", "context": "on smoking flights, four technicians"}, {"text": "92"}]}
        rep = grade.grade_page(self.truth, None, out)
        self.assertEqual(rep["correct"], 1)


class OptionPages(unittest.TestCase):
    schema = {"questions": [
        {"id": "q1", "select": "one", "options": [{"label": "YES"}, {"label": "NO"}]},
        {"id": "q2", "select": "one", "options": [{"label": "YES"}, {"label": "NO"}]},
        {"id": "q3", "select": "one", "options": [{"label": "Better", "code": "1"}, {"label": "Worse", "code": "2"}]},
        {"id": "q4", "select": "many", "options": [{"label": "Coffee"}, {"label": "Beer"}, {"label": "Mouth wash"}]}]}
    truth = {"page_id": "x", "kind": "options", "answers": [
        {"id": "1", "question_id": "q1", "expected": "YES", "case_type": []},
        {"id": "2", "question_id": "q2", "expected": None, "case_type": []},
        {"id": "3", "question_id": "q3", "expected": "Worse", "case_type": []},
        {"id": "4", "question_id": "q4", "expected": ["Coffee", "Mouth wash"], "case_type": []}]}

    def test_all_correct_with_code_and_null(self):
        out = {"answers": {"q1": "yes", "q2": None, "q3": "2", "q4": ["mouth wash", "Coffee"]}}
        self.assertEqual(grade.grade_page(self.truth, self.schema, out)["correct"], 4)

    def test_null_is_wrong_when_something_was_circled(self):
        out = {"answers": {"q1": None, "q2": "NO", "q3": "Better", "q4": ["Coffee"]}}
        self.assertEqual(grade.grade_page(self.truth, self.schema, out)["correct"], 0)


class RealData(unittest.TestCase):
    def test_oracle_scores_100_on_every_page(self):
        from pipelines import oracle
        for pid in data.all_page_ids():
            truth, schema = data.load_truth(pid), data.load_schema(pid)
            task = {"page_id": pid, "kind": truth["kind"], "schema": schema}
            self.assertEqual(grade.grade_page(truth, schema, oracle.run(task))["accuracy"], 1.0, pid)

    def test_every_expected_option_exists_in_schema(self):
        for pid in data.all_page_ids():
            truth, schema = data.load_truth(pid), data.load_schema(pid)
            if truth["kind"] != "options":
                continue
            qs = {q["id"]: q for q in schema["questions"]}
            for a in truth["answers"]:
                q = qs[a["question_id"]]
                exp = a["expected"]
                for e in (exp if isinstance(exp, list) else [exp]):
                    if e is not None and q["select"] != "text":
                        self.assertIn(e, [o["label"] for o in q["options"]], f"{pid} {a['id']}")


if __name__ == "__main__":
    unittest.main()
