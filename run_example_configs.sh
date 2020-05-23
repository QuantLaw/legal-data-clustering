#!/bin/bash

# Complexity paper
python . de preprocess cluster --number-of-modules 100 --consensus 1000
python . us preprocess cluster --number-of-modules 100 --consensus 1000

# Thesis

## Vergleich der Algorithmen
python . de preprocess cluster --clustering-method louvain infomap --seed 1
python . us preprocess cluster --clustering-method louvain infomap --seed 1

## Verlgeich der Modelle
python . de preprocess cluster --clustering-method louvain --seed 1 --pp-co-occurrence -1 --pp-co-occurrence-type decision paragraph --snapshot 2018-01-01 --single-process --markov-time 3 2 1 0.7 0.5
python . de preprocess cluster --clustering-method infomap --seed 1 --pp-co-occurrence -1 --pp-co-occurrence-type decision paragraph --snapshot 2018-01-01 --single-process
python . de preprocess cluster --clustering-method louvain infomap --seed 1 --pp-co-occurrence 1 0.1 0.01 0.001 -2 --pp-co-occurrence-type paragraph --snapshot 2018-01-01 --single-process --markov-time 1 0.7 0.5
