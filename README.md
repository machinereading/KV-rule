# KV-rule

## About

KV-rule is a rule-based fact checker that makes weighted logical positive and negative rules, and uses them to calculate a truth score for a given triple.

For example, the triple (Wozniak, education, UC Berkely) is assigned the high truth score close to true since it is logically consistent with the triple (Wozniak, almaMater, UC Berkely) in a knowledge graph according to the positive rule (x, education, y) ← (x, almaMater y).

In contrast, the triple (Wozniak, birthPlace, Florida) is assigned the low truth score close to false since it is logically contradict to the path (Wozniak, birthPlace, California) ∧ (California, ≠, Florida) in a knowledge graph according to the negative rule ¬(x, birthPlace, y) ← (x, birthPlace, z) ∧ (z, ≠, y).

<img src="./images/figure-1.png" width="80%" height="80%">

## Prerequisite
* `python 3`
* `bottle` (optional)

## Data preparation

1. Download the compressed folder `inter.tar.bz2` [Link](https://drive.google.com/file/d/1fv0-V-QDI5bHqQaSZapGZw-UCHS_N0O-/view?usp=sharing).

2. The compressed folder `inter.tar.bz2` contains the knowledge graphs, English DBpedia and K-Box, and the pre-trained positive and negative rules.

3. Unzip the compressed folder `inter.tar.bz2` by the command `tar -jxvf inter.tar.bz2`.

4. Locate all the folders in the unzipped folder `inter` into the directory `inter` in the main repository.

## Licenses
* `CC BY-NC-SA` [Attribution-NonCommercial-ShareAlike](https://creativecommons.org/licenses/by-nc-sa/2.0/)
* If you want to commercialize this resource, [please contact to us](http://mrlab.kaist.ac.kr/contact)

## Publisher
[Machine Reading Lab](http://mrlab.kaist.ac.kr/) @ KAIST

## Contact
Jiseong Kim. `jiseong@kaist.ac.kr`, `jiseong@gmail.com`

## Acknowledgement
This work was supported by Institute of Information & Communications Technology Planning & Evaluation(IITP) grant funded by the Korea government(MSIT) (2013-2-00109, WiseKB: Big data based self-evolving knowledge base and reasoning platform)