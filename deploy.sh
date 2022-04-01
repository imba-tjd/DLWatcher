set -ex

case "$(git branch --show-current)" in master|main) echo "Running on a wrong branch." && exit 1; esac

python3 dlwatcher.py
mv data.html index.html
rm data_tmpl.html deploy.sh dlwatcher.py

if [ -z "$(git status -s)" ]; then exit; fi

git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config --local user.name  "GitHub Actions"
git add data.csv index.html
git commit -m "Update"
git push
