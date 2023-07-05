rm -rf docs/api
python docs/gen-api.py
cd docs
sphinx-build . _build
