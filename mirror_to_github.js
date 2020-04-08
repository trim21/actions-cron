const exec = require('@actions/exec').exec
const assert = require('assert')

const path = require('path')
const fs = require('fs')

async function main () {
  const ACCESS_TOKEN = process.env.ACCESS_TOKEN
  assert(ACCESS_TOKEN.length !== 0, 'no access token given')
  const cwd = process.cwd()
  const repos = { 
    'mit-6.824': 'https://e.coding.net/Trim21/mit-6.824.git',
 }
  for (const [repoName, url] of Object.entries(repos)) {
    const repoDir = path.join(cwd, repoName)
    if (fs.existsSync(repoDir)) {
      fs.rmdirSync(repoDir, { recursive: true })
    }
    await exec(`git clone --mirror ${url} ${repoDir}`
    )
    process.chdir(repoDir)
    await exec(
      `git remote add --mirror=push github https://${ACCESS_TOKEN}@github.com/Trim21/${repoName}.git`
    )
    await exec('git push github')

  }
}

main().catch((e) => {
  console.log(e)
  process.exit(1)
})
