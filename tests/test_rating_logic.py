
import unittest
# Mocking JobSpyTools to test logic without Playwright
class MockJobSpyTools:
    def _calculate_salary_penalty(self, salary_text: str) -> int:
        """
        Calculate penalty points based on salary.
        -1 point for every $10k less than $200k base salary.
        """
        if not salary_text:
            return 0 

        # Normalize text
        text = salary_text.lower().replace(",", "").replace("$", "")
        
        # Extract numbers (simple regex for "120k", "120000", "120-150k")
        multiplier = 1
        if "k" in text:
            multiplier = 1000
            text = text.replace("k", "")
        
        import re
        matches = re.findall(r"(\d+(?:\.\d+)?)", text)
        if not matches:
            return 0

        try:
            val = float(matches[0]) * multiplier
            
            # Heuristic: If hourly (< 200), convert to annual (x 2000)
            if val < 200:
                val *= 2000
            
            # Target is 200k
            target = 200000
            if val >= target:
                return 0
            
            # Deficit
            deficit = target - val
            # Points = deficit / 10000
            points = int(deficit / 10000)
            return -points
            
        except Exception:
            return 0

    def calculate_rating(self, job: dict) -> int:
        score = 0
        title = job.get("title", "").lower()
        snippet = job.get("snippet", "").lower() 
        location = job.get("location", "").lower()
        full_text = f"{title} {snippet}"
        
        if job.get("easy_apply"):
            score += 1
        if "contract" in title or "contract" in snippet:
            score += 1
        is_remote = False
        if "remote" in location or job.get("remote") is True:
            score += 1
            is_remote = True
        if "c#" in full_text or "c sharp" in full_text:
            score += 1
        if "c++" in full_text or "cpp" in full_text:
            score += 1
        # Recent Job Logic Mock - simplified for test
        date_text = job.get("date_posted", "").lower()
        if any(x in date_text for x in ["today", "just", "hour", "minute", "second", "new"]):
            score += 1
        else:
            import re
            match = re.search(r"(\d+)\s*d", date_text)
            if match:
                if int(match.group(1)) <= 3:
                     score += 1
        
        # Best Places Logic Mock
        BEST_PLACES_TO_WORK = {"google", "microsoft", "apple", "meta"} # simplified
        if job.get("company", "").lower() in BEST_PLACES_TO_WORK:
            score += 1

        is_hybrid = "hybrid" in location
        if not is_remote and not is_hybrid:
            score -= 1
        salary_text = job.get("salary", "")
        score += self._calculate_salary_penalty(salary_text)
        return score

class TestJobRating(unittest.TestCase):
    def setUp(self):
        self.tools = MockJobSpyTools()

    def test_salary_penalty(self):
        # > 200k -> 0 penalty
        self.assertEqual(self.tools._calculate_salary_penalty("$250,000"), 0)
        self.assertEqual(self.tools._calculate_salary_penalty("200k"), 0)
        
        # 190k -> -1
        self.assertEqual(self.tools._calculate_salary_penalty("$190,000"), -1)
        
        # 150k -> -5
        self.assertEqual(self.tools._calculate_salary_penalty("$150k - $180k"), -5)
        
        # 100k -> -10
        self.assertEqual(self.tools._calculate_salary_penalty("100k"), -10)
        
        # Hourly $50 -> $100k -> -10
        self.assertEqual(self.tools._calculate_salary_penalty("$50/hr"), -10)
        
        # Hourly $100 -> $200k -> 0
        self.assertEqual(self.tools._calculate_salary_penalty("$100/hr"), 0)
        
        # No salary -> 0
        self.assertEqual(self.tools._calculate_salary_penalty(""), 0)

    def test_job_rating(self):
        # Perfect job
        job_perfect = {
            "title": "Senior C# C++ Developer Contract",
            "snippet": "We need C# and C++ experts.",
            "location": "Remote",
            "salary": "$250k",
            "easy_apply": True
        }
        # Points: 
        # Easy Apply +1
        # Contract +1
        # Remote +1
        # C# +1
        # C++ +1
        # Onsite penalty 0
        # Salary penalty 0
        # Total: 5
        self.assertEqual(self.tools.calculate_rating(job_perfect), 5)

        # Terrible job
        job_bad = {
            "title": "Junior Java Dev",
            "snippet": "Java only.",
            "location": "Austin, TX", # Onsite implied
            "salary": "$100k",
            "easy_apply": False
        }
        # Points:
        # Easy Apply 0
        # Contract 0
        # Remote 0
        # C# 0
        # C++ 0
        # Onsite penalty -1 (Not remote, not hybrid)
        # Salary penalty -10 (100k < 200k)
        # Total: -11
        self.assertEqual(self.tools.calculate_rating(job_bad), -11)

        # Hybrid C# job
        job_hybrid = {
            "title": "C# Developer",
            "snippet": "Coding in C#",
            "location": "Hybrid - New York",
            "salary": "$150k",
        }
        # Points:
        # Easy Apply 0
        # Contract 0
        # Remote 0
        # C# +1
        # C++ 0
        # Onsite penalty 0 (Is hybrid)
        # Salary penalty -5
        # Total: -4
        self.assertEqual(self.tools.calculate_rating(job_hybrid), -4)

    def test_recent_job_rating(self):
        # Recent job (+1)
        job_recent = {
            "title": "C++ Dev",
            "snippet": "C++",
            "location": "Remote",
            "salary": "$200k",
            "date_posted": "2 days ago"
        }
        # Points:
        # C++ +1
        # Remote +1
        # Recent +1
        # Salary 0
        # Total: 3
        self.assertEqual(self.tools.calculate_rating(job_recent), 3)

        # Old job (0)
        job_old = {
            "title": "C++ Dev",
            "snippet": "C++",
            "location": "Remote",
            "salary": "$200k",
            "date_posted": "30 days ago"
        }
        # Points:
        # C++ +1
        # Remote +1
        # Recent 0
        # Salary 0
        # Total: 2
        self.assertEqual(self.tools.calculate_rating(job_old), 2)

    def test_best_place_rating(self):
        # Google (+1 for best place)
        job_google = {
            "title": "Software Engineer",
            "company": "Google",
            "location": "Mountain View, CA", # Onsite -1
            "salary": "$250k",
        }
        # Points:
        # C++ 0
        # C# 0
        # Remote 0
        # Recent 0
        # Best Place +1
        # Onsite -1
        # Salary 0
        # Total: 0
        self.assertEqual(self.tools.calculate_rating(job_google), 0)



if __name__ == '__main__':
    unittest.main()
