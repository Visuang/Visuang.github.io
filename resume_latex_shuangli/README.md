# Shuang Li Resume LaTeX Package

This folder contains the standalone LaTeX source for Shuang Li's Chinese resume.

## Build

Use XeLaTeX:

```bash
latexmk -xelatex ShuangLi.tex
```

or:

```bash
xelatex ShuangLi.tex
```

The main source file is `ShuangLi.tex`.

Required local fonts are included under `fonts/`, so the folder can be moved or
archived independently from the original resume directory.
