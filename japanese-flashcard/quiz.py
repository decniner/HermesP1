# Japanese Flashcard Quiz App
import random

class Flashcard:
    def __init__(self, japanese, english):
        self.japanese = japanese
        self.english = english

class Quiz:
    def __init__(self):
        self.flashcards = []
        self.score = 0
        self.total = 0

    def add_card(self, japanese, english):
        self.flashcards.append(Flashcard(japanese, english))

    def load_defaults(self):
        cards = [
            ("こんにちは", "hello"),
            ("ありがとう", "thank you"),
            ("さようなら", "goodbye"),
            ("おはよう", "good morning"),
            ("おやすみ", "good night"),
            ("すみません", "excuse me"),
            ("はい", "yes"),
            ("いいえ", "no"),
            ("おいしい", "delicious"),
            ("たすけて", "help"),
        ]
        for j, e in cards:
            self.add_card(j, e)

    def run_quiz(self, num_questions=5):
        if not self.flashcards:
            return "No flashcards loaded!"

        selected = random.sample(self.flashcards, min(num_questions, len(self.flashcards)))
        self.score = 0
        self.total = len(selected)

        questions = []
        for card in selected:
            show_japanese = random.choice([True, False])

            if show_japanese:
                prompt = f"What does '{card.japanese}' mean?"
                correct = card.english
            else:
                prompt = f"How do you say '{card.english}' in Japanese?"
                correct = card.japanese

            questions.append((prompt, correct))

        return questions

    def get_score(self):
        if self.total == 0:
            return 0
        return round((self.score / self.total) * 100)

    def reset(self):
        self.score = 0
        self.total = 0


def main():
    quiz = Quiz()
    quiz.load_defaults()

    print("=" * 40)
    print("  🇯🇵 Japanese Flashcard Quiz")
    print("=" * 40)

    while True:
        questions = quiz.run_quiz(num_questions=5)
        if isinstance(questions, str):
            print(questions)
            return

        for prompt, correct in questions:
            print(f"\n{prompt}")
            answer = input("Your answer: ").strip().lower()

            if answer == correct.lower():
                print("  ✅ Correct!")
                quiz.score += 1
            else:
                print(f"  ❌ Wrong! Answer: {correct}")

        print(f"\n{'=' * 40}")
        print(f"  Score: {quiz.get_score()}% ({quiz.score}/{quiz.total})")
        print(f"{'=' * 40}")

        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("  またね! (See you next time!)")
            break


if __name__ == "__main__":
    main()
