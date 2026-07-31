export type ProfileId = "preview" | "demo" | "deep";
export type JobState = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export interface ConfigProfile {
  id: ProfileId;
  label: string;
  description: string;
  model: string;
  roleQuestionCount: number;
  hrQuestionCount: number;
  defaultAnswerCount: number;
  maxAnswerCount: number;
  maxIterations: number;
  passScore: number;
}

export interface PublicConfig {
  appVersion: string;
  buildTag: string;
  profiles: ConfigProfile[];
  defaultProfile: ProfileId;
  maxUploadBytes: number;
  supportedExtensions: string[];
  sessionIdleMinutes: number;
}

export interface Session {
  sessionId: string;
  profile: ProfileId;
  state: "evidence_ready" | "plan_ready" | "report_ready";
  createdAt: string;
  expiresInSeconds: number;
  activeJobId: string | null;
  hasPlan: boolean;
  hasReport: boolean;
  jobDescriptionFilename: string;
  candidateFilename: string | null;
}

export interface WorkflowJob {
  jobId: string;
  sessionId: string;
  type: "plan" | "answers";
  state: JobState;
  stage: string;
  message: string;
  completedSteps: number;
  totalSteps: number;
  errorCode: string | null;
  retryable: boolean;
  resultUrl: string | null;
}

export interface InterviewQuestion {
  questionId: string;
  group: "role_company" | "hr";
  category: string;
  question: string;
  rationale: string;
  strongAnswerSignals: string[];
  sourceIds: string[];
}

export interface RequirementAssessment {
  requirement: string;
  category: "must_have" | "preferred" | "competency";
  status: "matched" | "partial" | "gap" | "unknown";
  evidence: string;
  confidence: number;
}

export interface SearchSource {
  sourceId: string;
  title: string;
  url: string;
  snippet: string;
  published: string;
}

export interface InterviewPackage {
  identity: {
    companyName: string;
    roleTitle: string;
    confidence: string;
    evidence: string;
  };
  companyResearch: {
    companyName: string;
    summary: string;
    facts: Array<{ topic: string; finding: string; sourceIds: string[] }>;
    interviewTalkingPoints: string[];
    researchLimits: string[];
    sources: SearchSource[];
  };
  jdAnalysis: {
    roleTitle: string;
    seniority: string;
    roleSummary: string;
    responsibilities: string[];
    mustHaveSkills: string[];
    preferredSkills: string[];
    competencies: string[];
    likelyChallenges: string[];
    keywords: string[];
    candidateStrengths: string[];
    candidateGaps: string[];
    requirementAssessments: RequirementAssessment[];
  };
  interviewPlan: {
    companyName: string;
    roleTitle: string;
    roleCompanyQuestions: InterviewQuestion[];
    hrQuestions: InterviewQuestion[];
  };
  options: {
    roleQuestionCount: number;
    hrQuestionCount: number;
    maxIterations: number;
    answerWordLimit: number;
    webResearch: boolean;
  };
  jobFitMetrics: {
    overallPercent: number;
    mustHavePercent: number;
    preferredPercent: number;
    competencyPercent: number;
    evidenceCoveragePercent: number;
    assessmentConfidencePercent: number;
    matchedCount: number;
    partialCount: number;
    gapCount: number;
    unknownCount: number;
    assessedCount: number;
  };
  questionQualityMetrics: {
    totalQuestions: number;
    jdGroundedPercent: number;
    companyGroundedPercent: number;
    overallQualityPercent: number;
  };
}

export interface AnswerDraft {
  questionId: string;
  answer: string;
  evidenceUsed: string[];
  missingEvidence: string[];
  revision: number;
}

export interface AnswerEvaluation {
  questionId: string;
  score: number;
  strengths: string[];
  weaknesses: string[];
  unsupportedClaims: string[];
  improvementInstructions: string[];
}

export interface InterviewReport {
  package: InterviewPackage;
  answers: AnswerDraft[];
  evaluations: AnswerEvaluation[];
  iterationsCompleted: number;
  stoppedEarly: boolean;
  answerQualityMetrics: {
    answeredCount: number;
    averageScore: number;
    scorePercent: number;
    passingRatePercent: number;
    evidenceUsagePercent: number;
    unsupportedClaimRatePercent: number;
    answersNeedingImprovement: number;
  };
  generatedAt: string;
}
