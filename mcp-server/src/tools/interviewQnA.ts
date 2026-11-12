/**
 * Interview Q&A tool — retrieves role-specific interview Q&A pairs.
 */

export interface QnAPair {
  question: string;
  answer: string;
  topic: string;
  difficulty: "Easy" | "Medium" | "Hard";
  type: "Technical" | "Behavioral" | "HR" | "System Design";
}

const QNA_BANK: QnAPair[] = [
  // Technical — Python
  { question: "What is the difference between a list and a tuple in Python?", answer: "Lists are mutable (can be changed after creation) while tuples are immutable. Lists use square brackets [], tuples use parentheses (). Tuples are faster and are used for fixed data. Lists support append, remove, etc.", topic: "Python", difficulty: "Easy", type: "Technical" },
  { question: "Explain Python's GIL (Global Interpreter Lock).", answer: "GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes simultaneously. It means Python threads can't achieve true parallelism in CPU-bound tasks, but multiprocessing can be used instead.", topic: "Python", difficulty: "Medium", type: "Technical" },
  // Technical — DSA
  { question: "What is the time complexity of binary search?", answer: "O(log n). Binary search halves the search space with each comparison by requiring a sorted array.", topic: "DSA", difficulty: "Easy", type: "Technical" },
  { question: "Explain the difference between BFS and DFS.", answer: "BFS (Breadth-First Search) explores neighbors level by level using a queue — ideal for finding shortest paths. DFS (Depth-First Search) explores as deep as possible using a stack/recursion — ideal for topological sort, cycle detection.", topic: "DSA", difficulty: "Medium", type: "Technical" },
  // System Design
  { question: "How would you design a URL shortener like bit.ly?", answer: "Key components: API server, hash generation (base62 encoding of auto-increment ID), database (NoSQL like DynamoDB for speed), cache (Redis for popular URLs), load balancer. Handle collisions, expiration, analytics.", topic: "System Design", difficulty: "Hard", type: "System Design" },
  { question: "What is horizontal vs vertical scaling?", answer: "Vertical scaling adds more power (CPU, RAM) to an existing server — simpler but has limits. Horizontal scaling adds more servers — more complex but virtually unlimited capacity and better fault tolerance.", topic: "System Design", difficulty: "Easy", type: "System Design" },
  // Behavioral
  { question: "Tell me about a time you solved a difficult problem.", answer: "Use the STAR method: Situation — describe the context. Task — what you needed to accomplish. Action — what specific steps you took. Result — what the outcome was, ideally quantified.", topic: "Behavioral", difficulty: "Medium", type: "Behavioral" },
  { question: "Why do you want to work at this company?", answer: "Research the company's products, culture, values, and recent news. Connect their mission to your personal goals and skills. Be specific — mention a product you admire or a problem you'd like to help solve.", topic: "HR", difficulty: "Easy", type: "HR" },
  // OOP
  { question: "Explain the four pillars of OOP.", answer: "1. Encapsulation — bundling data and methods, hiding internal state. 2. Inheritance — classes derive properties from parent classes. 3. Polymorphism — same interface for different data types. 4. Abstraction — hiding complex implementation, exposing simple interface.", topic: "OOP", difficulty: "Easy", type: "Technical" },
  // Database
  { question: "What is the difference between SQL and NoSQL?", answer: "SQL databases are relational, use structured schemas, support ACID transactions — best for structured data. NoSQL databases are non-relational, schema-flexible, horizontally scalable — best for unstructured/semi-structured data, high volumes.", topic: "Database", difficulty: "Easy", type: "Technical" },
];

export async function generateQnA(
  role: string,
  topic: string = "general",
  count: number = 5
): Promise<{ role: string; topic: string; questions: QnAPair[] }> {
  let filtered = QNA_BANK;

  if (topic && topic !== "general") {
    const topicLower = topic.toLowerCase();
    filtered = QNA_BANK.filter(
      (q) => q.topic.toLowerCase().includes(topicLower) || q.type.toLowerCase().includes(topicLower)
    );
  }

  if (filtered.length === 0) filtered = QNA_BANK;

  // Shuffle and take count
  const shuffled = filtered.sort(() => Math.random() - 0.5);
  return {
    role,
    topic,
    questions: shuffled.slice(0, count),
  };
}
