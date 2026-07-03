"""Tests for the Japanese Flashcard Quiz app"""
import pytest
from quiz import Quiz, Flashcard

class TestFlashcard:
    def test_create_flashcard(self):
        card = Flashcard("こんにちは", "hello")
        assert card.japanese == "こんにちは"
        assert card.english == "hello"

class TestQuiz:
    def test_add_card(self):
        quiz = Quiz()
        quiz.add_card("ありがとう", "thank you")
        assert len(quiz.flashcards) == 1
        assert quiz.flashcards[0].japanese == "ありがとう"

    def test_load_defaults(self):
        quiz = Quiz()
        quiz.load_defaults()
        assert len(quiz.flashcards) == 10

    def test_run_quiz_returns_list_of_questions(self):
        quiz = Quiz()
        quiz.add_card("すみません", "excuse me")
        quiz.add_card("ありがとう", "thank you")
        questions = quiz.run_quiz(num_questions=2)
        assert isinstance(questions, list)
        assert len(questions) == 2
        for prompt, correct in questions:
            assert prompt is not None
            assert correct is not None

    def test_run_quiz_honors_num_questions(self):
        quiz = Quiz()
        quiz.load_defaults()
        questions = quiz.run_quiz(num_questions=3)
        assert len(questions) == 3

    def test_score_starts_zero(self):
        quiz = Quiz()
        assert quiz.get_score() == 0

    def test_score_after_correct_answers(self):
        quiz = Quiz()
        quiz.add_card("おはよう", "good morning")
        quiz.add_card("おやすみ", "good night")
        quiz.score = 2
        quiz.total = 2
        assert quiz.get_score() == 100

    def test_score_after_partial_answers(self):
        quiz = Quiz()
        quiz.add_card("はい", "yes")
        quiz.add_card("いいえ", "no")
        quiz.add_card("おいしい", "delicious")
        quiz.score = 1
        quiz.total = 3
        assert quiz.get_score() == 33

    def test_empty_quiz_returns_string_message(self):
        quiz = Quiz()
        result = quiz.run_quiz()
        assert isinstance(result, str)
        assert "No flashcards" in result

    def test_run_quiz_random_direction(self):
        """Test that questions come in both Japanese→English and English→Japanese"""
        quiz = Quiz()
        quiz.add_card("テスト", "test")
        quiz.add_card("サンプル", "sample")
        quiz.add_card("コード", "code")

        japanese_prompts = 0
        english_prompts = 0

        for _ in range(20):
            questions = quiz.run_quiz(num_questions=1)
            prompt, correct = questions[0]
            if "mean" in prompt.lower():
                japanese_prompts += 1
            else:
                english_prompts += 1

        # Both directions should appear over 20 runs
        assert japanese_prompts > 0
        assert english_prompts > 0

    def test_reset(self):
        quiz = Quiz()
        quiz.score = 5
        quiz.total = 10
        quiz.reset()
        assert quiz.score == 0
        assert quiz.total == 0
