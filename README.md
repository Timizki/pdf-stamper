# PDF stamper

Merges given pdf files to one file and stamps every input pdf with sequential number starting from 1

# Requirements to run
python 3
pip

# How to prepare
## Activate virtual env
Linux:
  source ./env/bin/active
Windows: (Not Tested)
 ./env/bin/active
 
## install  dependencies by running
pip install -r requirements.txt


# How to run 
1) Copy input pdfs to ./pdfs directory
2) To start numbering from one run command
python main.py
2.1) To start numbering with offset run command
python main.py --offset 123 


