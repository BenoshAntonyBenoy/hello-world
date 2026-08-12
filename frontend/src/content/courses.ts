// Free courses per requirement, keyed by the skill slug that taxonomy.py
// derives from the canonical name.
//
// Hand-curated and front-end only: this is a personal site, so it does not need
// to travel through the API or the static export. Every URL below was opened
// and returned 200 on 12 Aug 2026 — links rot, so re-check before relying on it.

export interface Course {
  title: string
  provider: string
  url: string
}

export const COURSES: Record<string, Course[]> = {
  python: [
    { title: 'Python', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/python' },
    { title: 'CS50’s Introduction to Programming with Python', provider: 'Harvard CS50', url: 'https://cs50.harvard.edu/python/' },
    { title: 'Scientific Computing with Python', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/scientific-computing-with-python/' },
  ],
  sql: [
    { title: 'Intro to SQL', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/intro-to-sql' },
    { title: 'Advanced SQL', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/advanced-sql' },
    { title: 'Relational Database', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/relational-database/' },
  ],
  javascript: [
    { title: 'JavaScript Algorithms and Data Structures', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/' },
  ],
  html: [
    { title: 'Responsive Web Design', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/2022/responsive-web-design/' },
  ],
  css: [
    { title: 'Responsive Web Design', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/2022/responsive-web-design/' },
  ],
  react: [
    { title: 'Front End Development Libraries', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/front-end-development-libraries/' },
  ],
  nodedotjs: [
    { title: 'Back End Development and APIs', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/back-end-development-and-apis/' },
  ],
  'rest-apis': [
    { title: 'Back End Development and APIs', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/back-end-development-and-apis/' },
  ],
  git: [
    { title: 'Introduction to version control with Git', provider: 'Microsoft Learn', url: 'https://learn.microsoft.com/en-us/training/paths/intro-to-vc-git/' },
  ],
  'data-structures-algorithms': [
    { title: 'CS201: Elementary Data Structures', provider: 'Saylor Academy', url: 'https://learn.saylor.org/course/CS201' },
    { title: 'JavaScript Algorithms and Data Structures', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/' },
    { title: 'Problem Solving (Basic) certification', provider: 'HackerRank', url: 'https://www.hackerrank.com/skills-verification/problem_solving_basic' },
  ],
  'problem-solving': [
    { title: 'Problem Solving (Basic) certification', provider: 'HackerRank', url: 'https://www.hackerrank.com/skills-verification/problem_solving_basic' },
    { title: 'CS50’s Introduction to Computer Science', provider: 'Harvard CS50', url: 'https://cs50.harvard.edu/x/' },
  ],
  'object-oriented-programming': [
    { title: 'CS50’s Introduction to Computer Science', provider: 'Harvard CS50', url: 'https://cs50.harvard.edu/x/' },
    { title: 'Python Essentials 1', provider: 'Cisco Networking Academy', url: 'https://www.netacad.com/courses/python-essentials-1' },
  ],
  'machine-learning': [
    { title: 'Intro to Machine Learning', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/intro-to-machine-learning' },
    { title: 'Machine Learning with Python', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/machine-learning-with-python/' },
  ],
  'deep-learning': [
    { title: 'Intro to Deep Learning', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/intro-to-deep-learning' },
    { title: 'CS50’s Introduction to AI with Python', provider: 'Harvard CS50', url: 'https://cs50.harvard.edu/ai/' },
  ],
  pandas: [
    { title: 'Pandas', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/pandas' },
    { title: 'Data Analysis with Python', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/data-analysis-with-python/' },
  ],
  statistics: [
    { title: 'MA121: Introduction to Statistics', provider: 'Saylor Academy', url: 'https://learn.saylor.org/course/MA121' },
  ],
  'data-visualization': [
    { title: 'Data Visualization', provider: 'Kaggle Learn', url: 'https://www.kaggle.com/learn/data-visualization' },
  ],
  excel: [
    { title: 'Excel training', provider: 'Microsoft Learn', url: 'https://learn.microsoft.com/en-us/training/browse/?products=office-excel' },
  ],
  'power-bi': [
    { title: 'Power BI learning paths', provider: 'Microsoft Learn', url: 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi' },
  ],
  docker: [
    { title: 'Docker Essentials', provider: 'IBM Cognitive Class', url: 'https://cognitiveclass.ai/courses/docker-essentials' },
  ],
  linux: [
    { title: 'Linux Essentials', provider: 'Cisco Networking Academy', url: 'https://www.netacad.com/courses/linux-essentials' },
  ],
  azure: [
    { title: 'Azure Fundamentals', provider: 'Microsoft Learn', url: 'https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/' },
  ],
  aws: [
    { title: 'Free digital training', provider: 'AWS Skill Builder', url: 'https://skillbuilder.aws/' },
  ],
  'google-cloud': [
    { title: 'Skill badge catalog', provider: 'Google Cloud Skills Boost', url: 'https://www.cloudskillsboost.google/catalog' },
  ],
  'network-security': [
    { title: 'Introduction to Cybersecurity', provider: 'Cisco Networking Academy', url: 'https://www.netacad.com/courses/introduction-to-cybersecurity' },
    { title: 'Networking Basics', provider: 'Cisco Networking Academy', url: 'https://www.netacad.com/courses/networking-basics' },
  ],
  'penetration-testing': [
    { title: 'Ethical Hacker', provider: 'Cisco Networking Academy', url: 'https://www.netacad.com/courses/ethical-hacker' },
    { title: 'Information Security', provider: 'freeCodeCamp', url: 'https://www.freecodecamp.org/learn/information-security/' },
  ],
  seo: [
    { title: 'SEO Certification', provider: 'HubSpot Academy', url: 'https://academy.hubspot.com/courses/seo-training' },
    { title: 'SEO courses', provider: 'Semrush Academy', url: 'https://www.semrush.com/academy/' },
  ],
  sem: [
    { title: 'Google Ads certifications', provider: 'Google Skillshop', url: 'https://skillshop.withgoogle.com/' },
  ],
  'content-marketing': [
    { title: 'Content Marketing', provider: 'HubSpot Academy', url: 'https://academy.hubspot.com/courses/content-marketing' },
  ],
  'email-marketing': [
    { title: 'Email Marketing', provider: 'HubSpot Academy', url: 'https://academy.hubspot.com/courses/email-marketing' },
  ],
  'google-analytics': [
    { title: 'Google Analytics Certification', provider: 'Google Skillshop', url: 'https://skillshop.withgoogle.com/' },
  ],
  microcontrollers: [
    { title: 'Arduino Education', provider: 'Arduino', url: 'https://www.arduino.cc/education' },
  ],
  communication: [
    { title: 'Free courses with a Statement of Participation', provider: 'The Open University', url: 'https://www.open.edu/openlearn/free-courses' },
  ],
  'requirements-gathering': [
    { title: 'SkillsBuild course catalog', provider: 'IBM SkillsBuild', url: 'https://skillsbuild.org/students/course-catalog' },
  ],
}
