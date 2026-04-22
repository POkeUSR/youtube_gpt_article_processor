base = """This is a test paragraph about AI and technology. Artificial intelligence is transforming the world. Machine learning models like GPT-4 are capable of understanding and generating human-like text. The future of AI is bright and full of opportunities. We need to adapt to these changes and learn new skills. Technology evolves rapidly and we must keep up with innovation. Otherwise we risk falling behind in this competitive landscape. AI can help solve complex problems in science, medicine, and engineering. But it also raises ethical questions we must address. The key is to use AI responsibly and for the benefit of all humanity."""

# Создаём большой текст: 200 похожих абзацев
text = "\n\n".join([base] * 250)
with open("gpt_text.txt", "w", encoding="utf-8") as f:
    f.write(text)
print(f"Created gpt_text.txt: {len(text)} chars, ~{len(text.split())} words")
