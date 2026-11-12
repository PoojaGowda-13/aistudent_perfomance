/**
 * MCP Server entry point — registers all tools for the Student AI Platform.
 * Tools: search_jobs, parse_resume_pdf, lookup_courses, get_student_marks,
 *        search_career_info, ats_check, generate_qna, store_agent_output
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { searchJobs } from "./tools/jobSearch.js";
import { lookupCourses } from "./tools/courseLookup.js";
import { generateQnA } from "./tools/interviewQnA.js";

const server = new Server(
  { name: "student-ai-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// ─── Tool Definitions ──────────────────────────────────────────────────────────

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "search_jobs",
      description: "Search for job listings based on role and location. Returns live job postings with required skills.",
      inputSchema: {
        type: "object",
        properties: {
          role: { type: "string", description: "Job role to search for (e.g. 'Software Engineer')" },
          location: { type: "string", description: "Location filter (e.g. 'Bangalore, India')" },
          limit: { type: "number", description: "Maximum number of results (default 10)" },
        },
        required: ["role"],
      },
    },
    {
      name: "lookup_courses",
      description: "Search for online courses by skill or topic. Returns courses from Coursera, Udemy, NPTEL.",
      inputSchema: {
        type: "object",
        properties: {
          skill: { type: "string", description: "Skill or topic to find courses for" },
          platform: { type: "string", description: "Platform filter: coursera/udemy/nptel/any" },
          max_results: { type: "number", description: "Max results (default 5)" },
        },
        required: ["skill"],
      },
    },
    {
      name: "generate_qna",
      description: "Retrieve interview Q&A pairs for a given role and topic from the knowledge bank.",
      inputSchema: {
        type: "object",
        properties: {
          role: { type: "string", description: "Target job role" },
          topic: { type: "string", description: "Topic/skill area (e.g. 'System Design', 'Python')" },
          count: { type: "number", description: "Number of Q&A pairs to return (default 5)" },
        },
        required: ["role"],
      },
    },
    {
      name: "search_career_info",
      description: "Search for career industry insights, role descriptions, and salary data.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Career research query" },
        },
        required: ["query"],
      },
    },
    {
      name: "ats_check",
      description: "Check resume text against a job description for ATS keyword match score.",
      inputSchema: {
        type: "object",
        properties: {
          resume_text: { type: "string", description: "Plain text content of the resume" },
          job_description: { type: "string", description: "Job description to match against" },
        },
        required: ["resume_text", "job_description"],
      },
    },
  ],
}));

// ─── Tool Execution ────────────────────────────────────────────────────────────

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "search_jobs": {
        const result = await searchJobs(
          args.role as string,
          (args.location as string) || "India",
          (args.limit as number) || 10
        );
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      }

      case "lookup_courses": {
        const result = await lookupCourses(
          args.skill as string,
          (args.platform as string) || "any",
          (args.max_results as number) || 5
        );
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      }

      case "generate_qna": {
        const result = await generateQnA(
          args.role as string,
          (args.topic as string) || "general",
          (args.count as number) || 5
        );
        return { content: [{ type: "text", text: JSON.stringify(result) }] };
      }

      case "search_career_info": {
        // Simulated career info search (replace with Brave Search MCP in production)
        const query = args.query as string;
        const mockResult = {
          query,
          results: [
            {
              title: `Career Overview: ${query}`,
              snippet: `Comprehensive information about ${query} career paths, required skills, salary ranges, and growth prospects in the Indian and global job market.`,
              source: "career_database",
            },
          ],
        };
        return { content: [{ type: "text", text: JSON.stringify(mockResult) }] };
      }

      case "ats_check": {
        const resumeText = (args.resume_text as string).toLowerCase();
        const jd = (args.job_description as string).toLowerCase();
        const jdWords = jd.match(/\b\w{4,}\b/g) || [];
        const uniqueKeywords = [...new Set(jdWords)];
        const matches = uniqueKeywords.filter((kw) => resumeText.includes(kw));
        const score = Math.min(100, Math.round((matches.length / Math.max(uniqueKeywords.length, 1)) * 100));
        const missing = uniqueKeywords.filter((kw) => !resumeText.includes(kw)).slice(0, 20);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ ats_score: score, matched_keywords: matches.slice(0, 20), missing_keywords: missing }),
            },
          ],
        };
      }

      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { content: [{ type: "text", text: `Tool error: ${message}` }], isError: true };
  }
});

// ─── Start Server ──────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Student AI MCP Server running on stdio");
}

main().catch(console.error);
