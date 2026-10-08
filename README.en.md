# Teaching Language Standard Skill

**paeg-teaching-language-skill** is the language-standard skill in the PAEG teaching-agent ecosystem. It provides an enforceable written-language standard and a zero-dependency checker for Chinese teaching materials: slide decks, handouts, lesson plans, worksheets, and teaching scripts.

## Standards referenced

- Law of the People's Republic of China on the Standard Spoken and Written Chinese Language
- **GB/T 15834—2011** *Usage of punctuation marks*
- **GB/T 15835—2011** *Usage of numerals in publications*
- Terminology of the *English Curriculum Standards for Senior High Schools (2017 edition, 2020 revision)*
- Research on teaching language: scientific, normative, educational, heuristic, and concise

## Problems addressed

AI-generated teaching text typically fails in five ways:

1. **Colloquialisms** — 才有, 要看, 谈不上, 查不到, 才是.
2. **Metaphor in place of definition** — "words are building materials", "the three burdens of a finite verb".
3. **Note-taking style** — "just remember that …", imperatives without a subject.
4. **Punctuation** — slashes or plus signs between coordinate words, half-width punctuation in Chinese, full stops after headings.
5. **Numerals and levels** — mixing 第1讲 with 第一讲, Arabic numerals for approximate numbers.

This skill turns those requirements into rule files, a forbidden-word list, a checker, and a rewrite corpus.

## Quick start

```bash
python -m paeg_teaching_language check handout.md
python -m paeg_teaching_language check ./materials --json report.json
python -m paeg_teaching_language fix handout.md --write
python -m unittest discover -s tests -v
python demo.py
```

## Repository layout

```
├─ SKILL.md                  skill definition loaded by agents
├─ README.md / README.en.md
├─ CHANGELOG.md
├─ LICENSE                   MIT
├─ demo.py                   one-minute demo
├─ docs/                     the standard, GB/T digests, before/after corpus, usage guide
├─ assets/                   printable self-check list
├─ src/paeg_teaching_language/
│   ├─ checker.py            linter
│   ├─ fixer.py              mechanical fixes
│   ├─ cli.py                command line interface
│   └─ data/                 extensible word lists and rules
└─ tests/                    15 unit tests
```

## Design principles

1. Every rule maps to an enumerable check with file, location, and matched text.
2. Word lists and toggles live in `data/*.json` so schools and subjects can extend them.
3. Automated checks are not the final review: metaphor, register, and coherence still need a human pass.
4. English example sentences and their translations are excluded from second-person and conjunction checks.
5. The checker uses only the Python standard library.

## License

MIT, see [LICENSE](LICENSE).
