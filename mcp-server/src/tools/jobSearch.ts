/**
 * Job Search tool — returns structured job listings for a given role.
 * In production, connect to LinkedIn Jobs API, Naukri API, or Indeed API.
 */

export interface JobListing {
  title: string;
  company: string;
  location: string;
  required_skills: string[];
  experience_years: string;
  salary_range: string;
  apply_url: string;
  posted_days_ago: number;
}

export async function searchJobs(
  role: string,
  location: string = "India",
  limit: number = 10
): Promise<{ role: string; location: string; total_found: number; listings: JobListing[] }> {
  // Simulated job listings (replace with real API call in production)
  const mockListings: JobListing[] = [
    {
      title: `${role}`,
      company: "Infosys",
      location: `${location}`,
      required_skills: ["Python", "SQL", "Machine Learning", "Communication"],
      experience_years: "0-2",
      salary_range: "₹4-8 LPA",
      apply_url: "https://www.infosys.com/careers",
      posted_days_ago: 2,
    },
    {
      title: `Junior ${role}`,
      company: "TCS",
      location: `${location}`,
      required_skills: ["Java", "Spring Boot", "MySQL", "Problem Solving"],
      experience_years: "0-1",
      salary_range: "₹3.5-6 LPA",
      apply_url: "https://www.tcs.com/careers",
      posted_days_ago: 5,
    },
    {
      title: `${role} - Fresher`,
      company: "Wipro",
      location: "Hyderabad",
      required_skills: ["JavaScript", "React", "Node.js", "REST API"],
      experience_years: "0",
      salary_range: "₹3-5 LPA",
      apply_url: "https://careers.wipro.com",
      posted_days_ago: 1,
    },
    {
      title: `Associate ${role}`,
      company: "Cognizant",
      location: "Chennai",
      required_skills: ["Python", "Data Analysis", "Excel", "PowerBI"],
      experience_years: "0-2",
      salary_range: "₹4-7 LPA",
      apply_url: "https://careers.cognizant.com",
      posted_days_ago: 3,
    },
    {
      title: `${role} Trainee`,
      company: "HCL Technologies",
      location: "Noida",
      required_skills: ["C++", "OOP", "DSA", "DBMS"],
      experience_years: "0",
      salary_range: "₹3-4.5 LPA",
      apply_url: "https://www.hcltech.com/careers",
      posted_days_ago: 7,
    },
  ];

  return {
    role,
    location,
    total_found: mockListings.length,
    listings: mockListings.slice(0, limit),
  };
}
