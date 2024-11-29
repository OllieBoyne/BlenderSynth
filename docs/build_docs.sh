rm -rf docs/api
python docs/gen_api.py
python docs/gen_rst.py
cd docs
export SPHINX_BUILD=1
sphinx-build . _build
python post.py
