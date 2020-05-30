#!/bin/bash

## Complexity paper
python . de preprocess cluster --number-of-modules 100 --consensus 1000
python . us preprocess cluster --number-of-modules 100 --consensus 1000

# Thesis

# Vergleich der Algorithmen
python . de preprocess cluster --clustering-method louvain infomap --seed 1 --snapshot 2018-01-01
python . us preprocess cluster --clustering-method louvain infomap --seed 1 --snapshot 2018

# Verlgeich der Modelle
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-co-occurrence -1 -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --markov-time 1 0.7

# Verlgeich des Detailgrads
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-ratio 5 --pp-merge 0 --pp-co-occurrence -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --markov-time 1
