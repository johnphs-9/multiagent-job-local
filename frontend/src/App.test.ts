import { describe, expect, it } from "vitest";
import { recommendedQuestionIds } from "./App";
import type { InterviewQuestion } from "./types";

function question(questionId: string): InterviewQuestion {
  return {
    questionId,
    group: questionId.startsWith("HR") ? "hr" : "role_company",
    category: "test",
    question: `Question ${questionId}`,
    rationale: "Test rationale",
    strongAnswerSignals: [],
    sourceIds: [],
  };
}

describe("recommended question selection", () => {
  it("selects all 26 Deep questions when they are available", () => {
    const roleQuestions = Array.from({ length: 20 }, (_, index) =>
      question(`RC${String(index + 1).padStart(2, "0")}`),
    );
    const hrQuestions = Array.from({ length: 6 }, (_, index) =>
      question(`HR${String(index + 1).padStart(2, "0")}`),
    );

    const selected = recommendedQuestionIds(roleQuestions, hrQuestions, 26);

    expect(selected).toHaveLength(26);
    expect(selected).toEqual([
      ...roleQuestions.map((item) => item.questionId),
      ...hrQuestions.map((item) => item.questionId),
    ]);
  });

  it("reserves one HR question for a smaller balanced recommendation", () => {
    const roleQuestions = Array.from({ length: 6 }, (_, index) =>
      question(`RC${String(index + 1).padStart(2, "0")}`),
    );
    const hrQuestions = [question("HR01"), question("HR02")];

    expect(recommendedQuestionIds(roleQuestions, hrQuestions, 4)).toEqual([
      "RC01",
      "RC02",
      "RC03",
      "HR01",
    ]);
  });

  it("keeps a balanced recommendation when only one HR question exists", () => {
    const roleQuestions = Array.from({ length: 6 }, (_, index) =>
      question(`RC${String(index + 1).padStart(2, "0")}`),
    );

    expect(
      recommendedQuestionIds(roleQuestions, [question("HR01")], 6),
    ).toEqual(["RC01", "RC02", "RC03", "RC04", "RC05", "HR01"]);
  });
});
