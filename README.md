# AIP Team6 - PDF RAG MEMO

Welcome to the **AIP Team6 - PDF RAG MEMO** repository!

## Overview

### Objective

1. **Enhancing Understanding of Learning Materials**
   Support students in better understanding documents such as research papers and textbooks in PDF format, which are commonly used for learning, through a RAG-based LLM QA system, enabling efficient review and note-taking.

2. **Providing an Intuitive Learning Tool**
   Allow users to immediately record ideas during the learning and research process without interruption through floating notes and flexible annotation and editing features.

### Features

1. **RAG-based Response Generation**
   Treat `[Source + User Query + LLM Response]` as a single `context chunk` and allow users to explicitly select or connect this chunk in the GUI to pass it to the LLM.

2. **Explicit and Easy Prompt/Context Control**
   Help users clearly define the prompt and context, enabling them to explicitly convey the intent of their queries to the LLM.

### Expected Benefits

1. **Performance Improvement**  
    By explicitly specifying prompts, users can clearly convey their intentions, thereby enhancing the performance of the LLM.
2. **Efficient Context Utilization**  
    Users can filter contexts to prevent context contamination and make efficient use of the context window.
3. **Convenient User Experience**  
    Users can intuitively view information and conversation flow at a glance, enabling more straightforward work.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/AIP_team6.git
    ```
2. Navigate to the project directory:
    ```bash
    cd AIP_Project
    ```
3. (Optional) Create and activate a virtual environment:
    ```bash
    python -m venv [your_venv]
    source [your_venv]/bin/activate  # On Windows: venv\Scripts\activate
    ```
4. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
How to run terminal demo (backend only)
```bash
cd AIP_team6
python .\src\backend\rag\demo.py
```

## License

This project is licensed under the [MIT License](LICENSE).

## Contact
...