rm -rf docs/api
python docs/gen_api.py
python docs/gen_rst.py
cd docs
sphinx-build . _build
