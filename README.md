# Multiagent Reinforcement Learning for Route Choice

This repository contains the source files of our research on Multiagent Reinforcement Learning (MARL) for route choice. The route choice problem models self-interested drivers that need to independently learn which routes minimise their expected travel costs. In this context, as drivers affect the reward perceived by each other, the optimal routes becomes a moving target. We approach this problem from the MARL perspective with a focus on theoretical performance guarantees. A list of algorithms resulting from this research is shown below.

This repository contains the following algorithms:

* **Regret Minimising Q-learning** (RMQ-learning), introduced in [1], which guaranteedly converges to a Nash equilibrium. See experiment `aamas17`.
* **Regret Minimising Q-learning with App Information**, introduced in [3], which investigates the impact of providing travel information to RMQ-learning agents. See experiment `trc18`.
* **Toll-based Q-learning** (TQ-learning), introduced in [2,6], which ensures that drivers converge to a Nash equilibrium aligned to the system's optimum. See experiment `ala18`.
* **Generalised Toll-based Q-learning** (GTQ-learning), introduced in [5,7], which extends TQ-learning to accommodate heterogeneous preferences, while allowing tax return and ensuring truthful preference reporting. See experiment `aamas20`.

## Publications

1. Ramos, G. de O., Silva, B. C. da, & Bazzan, A. L. C. (2017). **Learning to Minimise Regret in Route Choice**. In S. Das, E. Durfee, K. Larson, & M. Winikof (Eds.), *Proc. of the 16th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2017)* (pp. 846–855). São Paulo: IFAAMAS. [[link]](http://ifaamas.org/Proceedings/aamas2017/pdfs/p1855.pdf)

2. Ramos, G. de O., Silva, B. C., Rădulescu, R., & Bazzan, A. L. C. (2018). **Learning System-Efficient Equilibria in Route Choice Using Tolls**. In *Proc. of the Adaptive Learning Agents Workshop 2018 (ALA-18)*. Stockholm. [[link]](http://www.inf.ufrgs.br/maslab/pergamus/pubs/Ramos+2018ala.pdf)

3. Ramos, G. de O., Bazzan, A. L. C., & da Silva, B. C. (2018). **Analysing the impact of travel information for minimising the regret of route choice**. *Transportation Research Part C: Emerging Technologies*, 88, 257–271. [[link]](https://doi.org/10.1016/j.trc.2017.11.011)

4. Ramos, G. de O. (2018). **Regret Minimisation and System-Efficiency in Route Choice**. PhD thesis. Universidade Federal do Rio Grande do Sul. [[link]](http://hdl.handle.net/10183/178665)

5. Ramos, G., Rădulescu, R., & Nowé, A. (2019). **A Budged-Balanced Tolling Scheme for Efficient Equilibria under Heterogeneous Preferences**. In *Proc. of the Adaptive Learning Agents Workshop 2019 (ALA-19)*. Montreal. [[link]](https://ala2019.vub.ac.be/papers/ALA2019_paper_30.pdf)

6. Ramos, G. de O., Da Silva, B. C., Rădulescu, R., Bazzan, A. L. C., & Nowé, A. (2020). **Toll-based reinforcement learning for efficient equilibria in route choice**. *The Knowledge Engineering Review*, 35, e8. [[link]](https://doi.org/10.1017/S0269888920000119)

7. Ramos, G. de O., Rădulescu, R., Nowé, A., & Tavares, A. R. (2020). **Toll-Based Learning for Minimising Congestion under Heterogeneous Preferences**. In B. An, N. Yorke-Smith, A. E. F. Seghrouchni, & G. Sukthankar (Eds.), *Proc. of the 19th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2020)* (pp. 1098–1106). Auckland: IFAAMAS. [[link]](http://ifaamas.org/Proceedings/aamas2020/pdfs/p1098.pdf)


## Requirements

Before you begin, ensure you have met the following requirements:

* Python v2.7
* NumPy v1.15.1
* SciPy v1.1.0
* MatPlotLib v2.2.3
* SymPy v1.2
* [py-expression-eval v0.3.4](https://github.com/axiacore/py-expression-eval)

Newer versions of the above items may not be fully compatible with our code.

## Usage

To use marl-route-choice, you need to run `proof_of_concept.py` from the `marl-route-choice` directory and specify the desired parameters. To obtain help information, simply run the following command:

```bash
python proof_of_concept.py -h
```

From there, you can select the experiment you want to run (e.g., `aamas17`, `trc18`, `aamas20`) by simply specifying it as the first parameter. Note that each experiment has its own set of parameters. Help information is also available for each experiment by defining the experiment (e.g., `trc18`) followed by `-h`, as below:

```bash
python proof_of_concept.py trc18 -h
```

Finally, once an experiment is chosen, you can set the desired parameters. For instance, the command below runs the `weightedMCT` algorithm from the `aamas20` experiment on the `OW` network, with `12` routes per OD pair, for `10000` episodes. All unspecified parameters are set with their default values.

```bash
python proof_of_concept.py aamas20 --alg weightedMCT --net OW --k 12 --episodes 10000
```

At any time, you can validate the consistency of the source code with the original experiments by selecting option `--validate`. For instance, in order to validate the `aamas20` experiments, run the command below. Note that the validation procedures may take several minutes.

```bash
python proof_of_concept.py aamas20 --validate
```

In order to validate the consistency of all experiments, run:

```bash
python proof_of_concept.py --validate_all
```

## Road Networks

The road networks used in this project are available in the `networks` directory. All networks were specified following the [Transportation Networks](https://github.com/goramos/transportation_networks) project. 

## Contributors

Thanks to the following people who have contributed to this project:

* [Gabriel Ramos](https://gdoramos.net)
* [Roxana Rădulescu](https://github.com/rradules)

## How to cite this research

For citing this work, please use the following entries. For entries of the other works, go to [https://gdoramos.net/publications/](https://gdoramos.net/publications/).

```bibtex
@InProceedings{Ramos+2017aamas,
	author = {Ramos, Gabriel {\relax de} O. and {\relax da} Silva, Bruno C. and Bazzan, Ana L. C.},
	title = {Learning to Minimise Regret in Route Choice},
	booktitle = {Proc. of the 16th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2017)},
	pages = {846--855},
	year = {2017},
	editor = {S. Das and E. Durfee and K. Larson and M. Winikoff},
	address = {S\~ao Paulo, Brazil},
	month = {May},
	publisher = {IFAAMAS},
	url = {http://ifaamas.org/Proceedings/aamas2017/pdfs/p846.pdf}
}
```

```bibtex
@InProceedings{Ramos+2020aamas,
	author = {Ramos, Gabriel {\relax de} O. and R\u{a}dulescu, Roxana and Now\'e, Ann and Tavares, Anderson R.},
	title = {Toll-Based Learning for Minimising Congestion under Heterogeneous Preferences},
	booktitle = {Proc. of the 19th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2020)},
	pages = {1098--1106},
	year = {2020},
	editor = {An, B. and Yorke-Smith, N. and El Fallah Seghrouchni, A. and Sukthankar, G.},
	address = {Auckland, New Zealand},
	month = {May},
	publisher = {IFAAMAS},
	url = {http://ifaamas.org/Proceedings/aamas2020/pdfs/p1098.pdf}
}
```	

## License

This project uses the following license: [MIT](https://github.com/goramos/marl-route-choice/blob/f5a47bc5c6a791bf3d2eed48e13b5ca2a28fba5a/LICENSE).