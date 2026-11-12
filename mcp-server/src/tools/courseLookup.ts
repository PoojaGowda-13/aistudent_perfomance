/**
 * Course Lookup tool — returns relevant courses for a skill from multiple platforms.
 */

export interface Course {
  title: string;
  platform: string;
  instructor: string;
  duration_hours: number;
  rating: number;
  cost: "Free" | "Paid";
  url_hint: string;
  skill_tags: string[];
  level: "Beginner" | "Intermediate" | "Advanced";
}

const COURSE_DATABASE: Record<string, Course[]> = {
  python: [
    { title: "Python for Everybody", platform: "Coursera", instructor: "Dr. Chuck", duration_hours: 40, rating: 4.8, cost: "Free", url_hint: "coursera.org/specializations/python", skill_tags: ["Python", "Programming"], level: "Beginner" },
    { title: "100 Days of Code: Python Bootcamp", platform: "Udemy", instructor: "Angela Yu", duration_hours: 60, rating: 4.7, cost: "Paid", url_hint: "udemy.com/course/100-days-of-code", skill_tags: ["Python", "Web Dev", "Automation"], level: "Beginner" },
    { title: "Python Programming - NPTEL", platform: "NPTEL", instructor: "IIT Madras", duration_hours: 40, rating: 4.5, cost: "Free", url_hint: "nptel.ac.in/courses/106106182", skill_tags: ["Python", "DSA"], level: "Intermediate" },
  ],
  "machine learning": [
    { title: "Machine Learning Specialization", platform: "Coursera", instructor: "Andrew Ng", duration_hours: 120, rating: 4.9, cost: "Free", url_hint: "coursera.org/specializations/machine-learning-introduction", skill_tags: ["ML", "Python", "Statistics"], level: "Intermediate" },
    { title: "Machine Learning A-Z", platform: "Udemy", instructor: "Kirill Eremenko", duration_hours: 44, rating: 4.5, cost: "Paid", url_hint: "udemy.com/course/machinelearning", skill_tags: ["ML", "Python", "R"], level: "Beginner" },
  ],
  "data structures": [
    { title: "Data Structures and Algorithms", platform: "Coursera", instructor: "UC San Diego", duration_hours: 100, rating: 4.6, cost: "Free", url_hint: "coursera.org/specializations/data-structures-algorithms", skill_tags: ["DSA", "Algorithms", "Problem Solving"], level: "Intermediate" },
    { title: "DSA with Java - NPTEL", platform: "NPTEL", instructor: "IIT Kharagpur", duration_hours: 40, rating: 4.4, cost: "Free", url_hint: "nptel.ac.in/courses/106105085", skill_tags: ["DSA", "Java"], level: "Intermediate" },
  ],
  "system design": [
    { title: "Grokking the System Design Interview", platform: "educative.io", instructor: "Design Gurus", duration_hours: 15, rating: 4.7, cost: "Paid", url_hint: "educative.io/courses/grokking-system-design-interview", skill_tags: ["System Design", "Architecture"], level: "Advanced" },
  ],
  javascript: [
    { title: "The Complete JavaScript Course", platform: "Udemy", instructor: "Jonas Schmedtmann", duration_hours: 69, rating: 4.7, cost: "Paid", url_hint: "udemy.com/course/the-complete-javascript-course", skill_tags: ["JavaScript", "ES6", "DOM"], level: "Beginner" },
    { title: "JavaScript Algorithms - freeCodeCamp", platform: "freeCodeCamp", instructor: "fCC Team", duration_hours: 300, rating: 4.8, cost: "Free", url_hint: "freecodecamp.org/learn/javascript-algorithms-and-data-structures", skill_tags: ["JavaScript", "DSA"], level: "Beginner" },
  ],
  react: [
    { title: "React - The Complete Guide", platform: "Udemy", instructor: "Maximilian Schwarzmüller", duration_hours: 48, rating: 4.7, cost: "Paid", url_hint: "udemy.com/course/react-the-complete-guide-incl-redux", skill_tags: ["React", "Redux", "Hooks"], level: "Intermediate" },
  ],
  sql: [
    { title: "SQL for Data Science", platform: "Coursera", instructor: "UC Davis", duration_hours: 16, rating: 4.6, cost: "Free", url_hint: "coursera.org/learn/sql-for-data-science", skill_tags: ["SQL", "Database", "Analytics"], level: "Beginner" },
  ],
};

export async function lookupCourses(
  skill: string,
  platform: string = "any",
  maxResults: number = 5
): Promise<{ skill: string; courses: Course[]; total: number }> {
  const skillLower = skill.toLowerCase();

  // Find best matching key
  let courses: Course[] = [];
  for (const [key, courselist] of Object.entries(COURSE_DATABASE)) {
    if (skillLower.includes(key) || key.includes(skillLower)) {
      courses = [...courses, ...courselist];
    }
  }

  // Filter by platform if specified
  if (platform !== "any") {
    courses = courses.filter((c) =>
      c.platform.toLowerCase().includes(platform.toLowerCase())
    );
  }

  // Default fallback
  if (courses.length === 0) {
    courses = [
      {
        title: `${skill} Fundamentals`,
        platform: "Coursera",
        instructor: "Top Instructors",
        duration_hours: 20,
        rating: 4.5,
        cost: "Free",
        url_hint: `coursera.org/search?query=${encodeURIComponent(skill)}`,
        skill_tags: [skill],
        level: "Beginner",
      },
    ];
  }

  return { skill, courses: courses.slice(0, maxResults), total: courses.length };
}
