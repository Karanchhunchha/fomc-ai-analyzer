import re

with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Enhance the top section
top_section = '''# FOMC AI Analyzer ???

<div align="center">

**An AI-Native Financial Intelligence Platform for Federal Reserve Policy Analysis**

[![MathWorks Challenge](https://img.shields.io/badge/MathWorks-Challenge%20%23258-E2231A?style=for-the-badge&logo=mathworks)](https://github.com/mathworks/MATLAB-Simulink-Challenge-Project-Hub/tree/main/projects/Federal%20Open%20Market%20Committee%20Minutes%20Analysis%20with%20Large%20Language%20Models)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=nextdotjs)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

[**Challenge Hub**](https://github.com/mathworks/MATLAB-Simulink-Challenge-Project-Hub/tree/main/projects/Federal%20Open%20Market%20Committee%20Minutes%20Analysis%20with%20Large%20Language%20Models) • [**Report Bug**](https://github.com/Karanchhunchha/fomc-ai-analyzer/issues) • [**Request Feature**](https://github.com/Karanchhunchha/fomc-ai-analyzer/issues)

<br>

**? If you find this project useful or insightful, please consider starring the repository! It helps the project grow! ?**

</div>

<div align="center">
  <img src="docs/ss1.png" alt="FOMC Terminal - Analysis" width="800" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px;"/>
  <br/><br/>
  <img src="docs/ss2.png" alt="FOMC Terminal - Citations" width="800" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</div>

*AI-native workspace featuring the transparent "Thinking Panel" and semantic citations.*

---
'''

# Replace from start to the first '---'
content = re.sub(r'^# FOMC AI Analyzer.*?---', top_section, content, flags=re.DOTALL)

# Add Star History at the end
star_history = '''
---

## ?? Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Karanchhunchha/fomc-ai-analyzer&type=Date)](https://star-history.com/#Karanchhunchha/fomc-ai-analyzer&Date)
'''
if '## ?? Star History' not in content:
    content += star_history

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)

