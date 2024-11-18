/**
 * @type {import('electron-builder').Configuration}
 * @see https://www.electron.build/configuration/configuration
 */
const config = {
  directories: {
    output: 'release',
    buildResources: 'build'
  },
  files: [
    'dist/**/*',
    'dist-electron/**/*'
  ],
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true
  }
}

module.exports = config 