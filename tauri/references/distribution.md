# Tauri - Distribution

**Pages:** 8

---

## Windows Code Signing

**URL:** llms-txt#windows-code-signing

**Contents:**
- OV Certificates
  - Prerequisites
  - Getting Started
  - Prepare `tauri.conf.json` file
  - Sign your application with GitHub Actions.
- Azure Key Vault
- Custom Sign Command
- Azure Code Signing
  - Prerequisites
  - Getting Started

import { Steps } from '@astrojs/starlight/components';

Code signing is required on Windows to allow your application to be listed in the [Microsoft Store] and to prevent a [SmartScreen] warning that your application is not trusted and can not be started, when downloaded from the browser.

It is not required to execute your application on Windows, as long as your end user is okay with ignoring the [SmartScreen] warning or your user does not download via the browser.
This guide covers signing via OV (Organization Validated) certificates and Azure Key Vault.
If you use any other signing mechanism not documented here, such as EV (Extended Validation) certificates,
check out your certificate issuer documentation and refer to the [custom sign command](#custom-sign-command) section.

This guide only applies to OV code signing certificates acquired before June 1st 2023! For code signing with EV certificates and OV certificates received after that date please consult the documentation of your certificate issuer instead.

If you sign the app with an EV Certificate, it'll receive an immediate reputation with Microsoft SmartScreen and won't show any warnings to users.

If you opt for an OV Certificate, which is generally cheaper and available to individuals, Microsoft SmartScreen will still show a warning to users when they download the app. It might take some time until your certificate builds enough reputation. You may opt for [submitting your app] to Microsoft for manual review. Although not guaranteed, if the app does not contain any malicious code, Microsoft may grant additional reputation and potentially remove the warning for that specific uploaded file.

See the [comparison](https://www.digicert.com/difference-between-dv-ov-and-ev-ssl-certificates) to learn more about OV vs EV certificates.

- Windows - you can likely use other platforms, but this tutorial uses Powershell native features.
- A working Tauri application
- Code signing certificate - you can acquire one of these on services listed in [Microsoft's docs]. There are likely additional authorities for non-EV certificates than included in that list, please compare them yourself and choose one at your own risk.
  - Please make sure to get a **code signing** certificate, SSL certificates do not work!

There are a few things we have to do to get Windows prepared for code signing. This includes converting our certificate to a specific format, installing this certificate, and decoding the required information from the certificate.

1. #### Convert your `.cer` to `.pfx`
   - You will need the following:
     - certificate file (mine is `cert.cer`)
     - private key file (mine is `private-key.key`)

- Open up a command prompt and change to your current directory using `cd Documents/Certs`

- Convert your `.cer` to a `.pfx` using `openssl pkcs12 -export -in cert.cer -inkey private-key.key -out certificate.pfx`

- You should be prompted to enter an export password **DON'T FORGET IT!**

2. #### Import your `.pfx` file into the keystore.
   - We now need to import our `.pfx` file.

- Assign your export password to a variable using `$WINDOWS_PFX_PASSWORD = 'MYPASSWORD'`

- Now Import the certificate using `Import-PfxCertificate -FilePath certificate.pfx -CertStoreLocation Cert:\CurrentUser\My -Password (ConvertTo-SecureString -String $WINDOWS_PFX_PASSWORD -Force -AsPlainText)`

3. #### Prepare Variables
   - Start ➡️ `certmgr.msc` to open Personal Certificate Management, then open Personal/Certificates.

- Find the certificate we just imported and double-click on it, then click on the Details tab.

- The Signature hash algorithm will be our `digestAlgorithm`. (Hint: this is likely `sha256`)

- Scroll down to Thumbprint. There should be a value like `A1B1A2B2A3B3A4B4A5B5A6B6A7B7A8B8A9B9A0B0`. This is our `certificateThumbprint`.

- We also need a timestamp URL; this is a time server used to verify the time of the certificate signing. I'm using `http://timestamp.comodoca.com`, but whoever you got your certificate from likely has one as well.

### Prepare `tauri.conf.json` file

1. Now that we have our `certificateThumbprint`, `digestAlgorithm`, & `timestampUrl` we will open up the `tauri.conf.json`.

2. In the `tauri.conf.json` you will look for the `tauri` -> `bundle` -> `windows` section. There are three variables for the information we have captured. Fill it out like below.

3. Save and run `tauri build`

4. In the console output, you should see the following output.

Which shows you have successfully signed the `.exe`.

And that's it! You have successfully set up your Tauri application for Windows signing.

### Sign your application with GitHub Actions.

We can also create a workflow to sign the application with GitHub actions.

We need to add a few GitHub secrets for the proper configuration of the GitHub Action. These can be named however you would like.

- You can view the [encrypted secrets] guide on how to add GitHub secrets.

The secrets we used are as follows

|        GitHub Secrets        |                                                        Value for Variable                                                         |
| :--------------------------: | :-------------------------------------------------------------------------------------------------------------------------------: |
|     WINDOWS_CERTIFICATE      | Base64 encoded version of your .pfx certificate, can be done using this command `certutil -encode certificate.pfx base64cert.txt` |
| WINDOWS_CERTIFICATE_PASSWORD |                                 Certificate export password used on creation of certificate .pfx                                  |

#### Workflow Modifications

1. We need to add a step in the workflow to import the certificate into the Windows environment. This workflow accomplishes the following
   1. Assign GitHub secrets to environment variables
   2. Create a new `certificate` directory
   3. Import `WINDOWS_CERTIFICATE` into tempCert.txt
   4. Use `certutil` to decode the tempCert.txt from base64 into a `.pfx` file.
   5. Remove tempCert.txt
   6. Import the `.pfx` file into the Cert store of Windows & convert the `WINDOWS_CERTIFICATE_PASSWORD` to a secure string to be used in the import command.

2. We will be using the [`tauri-action` publish template].

3. Right above `-name: install app dependencies and build it` you will want to add the following step

4. Save and push to your repo.

5. Your workflow can now import your windows certificate and import it into the GitHub runner, allowing for automated code signing!

You can sign the Windows executables by providing an Azure Key Vault certificate and credentials.

:::note
This guide uses [relic] due to its support to secret-based authentication, though you can configure alternative tools if you prefer.
To download relic, check its [releases page][relic releases page] or run `go install github.com/sassoftware/relic/v8@latest`.
:::

In the [Azure Portal] navigate to the [Key vaults service] to create a new key vault by clicking the "Create" button.
Remember the "Key vault name" as you will need that information to configure the certificate URL.

After creating a key vault, select it and go to the "Objects > Certificates" page to create a new certificate and click the "Generate/Import" button.
Remember the "Certificate name" as you will need that information to configure the certificate URL.

3. Tauri Configuration

[relic] uses a configuration file to determine which signing key it should use. For Azure Key Vault you also need the certificate URL.
Create a `relic.conf` file in the `src-tauri` folder and configure relic to use your certificate:

Note that you must replace \<KEY_VAULT_NAME\> and \<CERTIFICATE_NAME\> with the appropriate names from the previous steps.

To configure Tauri to use your Azure Key Vault configuration for signing change the [bundle > windows > signCommand] config value:

[relic] must authenticate with Azure in order to load the certificate.
In the Azure portal landing page, go to the "Microsoft Entra ID" service and head to the "Manage > App registrations" page.
Click "New registration" to create a new app. After creating the app, you are redirected to the application details page where you can see the "Application (client) ID" and "Directory (tenant) ID" values.
Set these IDs to the `AZURE_CLIENT_ID` and `AZURE_TENANT_ID` environment variables respectively.

In the "Manage > Certificates & secrets" page click the "New client secret" button and set the text in the "Value" column as the `AZURE_CLIENT_SECRET` environment variable.

After setting up all the credentials, head back to your key vault's page and navigate to the "Access control (IAM)" page.
You must assign the "Key Vault Certificate User" and "Key Vault Crypto User" roles to your newly created application.

After setting up all these variables, running `tauri build` will produce signed Windows installers!

## Custom Sign Command

In the [Azure Key Vault](#azure-key-vault) documentation above we used a powerful Tauri Windows signing configuration to force the Tauri CLI to use
a special shell command to sign Windows installer executables. The [bundle > windows > signCommand] configuration option can be used to use any codesign tool
that can sign Windows executables.

:::tip
When cross compiling Windows installers from Linux and macOS machines, you **must** use a custom sign command as the default implementation only works on Windows machines.
:::

[Azure Portal]: https://portal.azure.com
[Key vaults service]: https://portal.azure.com/#browse/Microsoft.KeyVault%2Fvaults
[microsoft's docs]: https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-cert-manage
[submitting your app]: https://www.microsoft.com/en-us/wdsi/filesubmission/
[encrypted secrets]: https://docs.github.com/en/actions/reference/encrypted-secrets
[`tauri-action` publish template]: https://github.com/tauri-apps/tauri-action
[relic]: https://github.com/sassoftware/relic
[relic releases page]: https://github.com/sassoftware/relic/releases/
[bundle > windows > signCommand]: /reference/config/#signcommand
[SmartScreen]: https://en.wikipedia.org/wiki/Microsoft_SmartScreen
[Microsoft Store]: https://apps.microsoft.com/

## Azure Code Signing

You can sign the Windows executables by providing an Azure Code signing certificate and credentials. If you don't have an Azure Code signing Account yet you can follow this [tutorial](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/).

If you want to sign with Github Actions everything should be installed.

1. [Trusted Signing Account](https://learn.microsoft.com/en-us/azure/trusted-signing/quickstart?tabs=registerrp-portal,account-portal,certificateprofile-portal,deleteresources-portal) and permissions configured
1. [.NET](https://dotnet.microsoft.com/en-us/download/dotnet/8.0) (.NET 6 or later recommended)
1. [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli#install-or-update)
1. [Signtool](https://learn.microsoft.com/en-us/dotnet/framework/tools/signtool-exe) (Windows 11 SDK 10.0.22000.0 or later recommended)

You need to install [trusted-signing-cli](https://github.com/Levminer/trusted-signing-cli) and configure your environment variables.

1. #### Install trusted-signing-cli
   - `cargo install trusted-signing-cli`

2. #### Configure environment variables
   - trusted-signing-cli needs the following environment variables to be set, don't forget to add these as Github Actions [secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions):
     - `AZURE_CLIENT_ID`: The client ID of your [App Registration](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/#step-4-create-app-registration-user-credentials)
     - `AZURE_CLIENT_SECRET`: The client secret of [App Registration](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/#step-4-create-app-registration-user-credentials)
     - `AZURE_TENANT_ID`: The tenant ID of your Azure directory, you can also get this from your [App Registration](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/#step-4-create-app-registration-user-credentials)

3. ### Modify your `tauri.conf.json` file
   - You can modify your `tauri.conf.json` or you can create a specific config file for Windows. Replace the URL and the certificate name with your own values.
     - -e: The endpoint of your Azure Code Signing account
     - -a: The name of your Azure Code Signing Account
     - -c: The name of your Certificate profile inside your Azure Code Signing Account
     - -d: The description of the signed content (optional). When signing a .msi installer, this description will appear as the installer's name in the UAC prompt or will be a random string of characters if unset.

**Examples:**

Example 1 (unknown):
```unknown
3. Save and run `tauri build`

4. In the console output, you should see the following output.
```

Example 2 (unknown):
```unknown
Which shows you have successfully signed the `.exe`.

And that's it! You have successfully set up your Tauri application for Windows signing.

### Sign your application with GitHub Actions.

We can also create a workflow to sign the application with GitHub actions.

#### GitHub Secrets

We need to add a few GitHub secrets for the proper configuration of the GitHub Action. These can be named however you would like.

- You can view the [encrypted secrets] guide on how to add GitHub secrets.

The secrets we used are as follows

|        GitHub Secrets        |                                                        Value for Variable                                                         |
| :--------------------------: | :-------------------------------------------------------------------------------------------------------------------------------: |
|     WINDOWS_CERTIFICATE      | Base64 encoded version of your .pfx certificate, can be done using this command `certutil -encode certificate.pfx base64cert.txt` |
| WINDOWS_CERTIFICATE_PASSWORD |                                 Certificate export password used on creation of certificate .pfx                                  |

#### Workflow Modifications

1. We need to add a step in the workflow to import the certificate into the Windows environment. This workflow accomplishes the following
   1. Assign GitHub secrets to environment variables
   2. Create a new `certificate` directory
   3. Import `WINDOWS_CERTIFICATE` into tempCert.txt
   4. Use `certutil` to decode the tempCert.txt from base64 into a `.pfx` file.
   5. Remove tempCert.txt
   6. Import the `.pfx` file into the Cert store of Windows & convert the `WINDOWS_CERTIFICATE_PASSWORD` to a secure string to be used in the import command.

2. We will be using the [`tauri-action` publish template].
```

Example 3 (unknown):
```unknown
3. Right above `-name: install app dependencies and build it` you will want to add the following step
```

Example 4 (unknown):
```unknown
4. Save and push to your repo.

5. Your workflow can now import your windows certificate and import it into the GitHub runner, allowing for automated code signing!

## Azure Key Vault

You can sign the Windows executables by providing an Azure Key Vault certificate and credentials.

:::note
This guide uses [relic] due to its support to secret-based authentication, though you can configure alternative tools if you prefer.
To download relic, check its [releases page][relic releases page] or run `go install github.com/sassoftware/relic/v8@latest`.
:::

1. Key Vault

In the [Azure Portal] navigate to the [Key vaults service] to create a new key vault by clicking the "Create" button.
Remember the "Key vault name" as you will need that information to configure the certificate URL.

2. Certificate

After creating a key vault, select it and go to the "Objects > Certificates" page to create a new certificate and click the "Generate/Import" button.
Remember the "Certificate name" as you will need that information to configure the certificate URL.

3. Tauri Configuration

[relic] uses a configuration file to determine which signing key it should use. For Azure Key Vault you also need the certificate URL.
Create a `relic.conf` file in the `src-tauri` folder and configure relic to use your certificate:
```

---

## GitHub

**URL:** llms-txt#github

**Contents:**
- Getting Started
- Configuration
  - How to Trigger
- Example Workflow
- Arm Runner Compilation
- Troubleshooting
  - GitHub Environment Token

This guide will show you how to use [tauri-action](https://github.com/tauri-apps/tauri-action) in [GitHub Actions](https://docs.github.com/en/actions) to easily build and upload your app, and how to make Tauri's updater query the newly created GitHub release for updates.

Lastly, it will also show how to set up a more complicated build pipeline for Linux Arm AppImages.

:::note[Code Signing]

To set up code signing for Windows and macOS in your workflow, follow the specific guide for each platform:

- [Windows Code Signing](/distribute/sign/windows/)
- [macOS Code Signing](/distribute/sign/macos/)

To set up `tauri-action` you must first set up a GitHub repository. You can also use this action on a repository that does not have Tauri configured yet since it can automatically initialize Tauri for you, please see the [action's readme](https://github.com/tauri-apps/tauri-action/#project-initialization) for necessary configuration options.

Go to the Actions tab on your GitHub project page and select "New workflow", then choose "Set up a workflow yourself". Replace the file with the workflow from [below](#example-workflow) or from one of the [action's examples](https://github.com/tauri-apps/tauri-action/tree/dev/examples).

Please see the `tauri-action` [readme](https://github.com/tauri-apps/tauri-action/#inputs) for all available configuration options.

When your app is not on the root of the repository, use the `projectPath` input.

You may freely modify the workflow name, change its triggers, and add more steps such as `npm run lint` or `npm run test`. The important part is that you keep the below line at the end of the workflow since this runs the build script and releases your app.

The release workflow shown below and in the `tauri-action` examples is triggered by pushed to the `release` branch. The action automatically creates a git tag and a title for the GitHub release using the application version.

As another example, you can also change the trigger to run the workflow on the push of a version git tag such as `app-v0.7.0`:

For a full list of possible trigger configurations, check out the official [GitHub documentation](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows).

Below is an example workflow that has been set up to run every time you push to the `release` branch.

This workflow will build and release your app for Windows x64, Linux x64, Linux Arm64, macOS x64 and macOS Arm64 (M1 and above).

The steps this workflow takes are:

1. Checkout the repository using `actions/checkout@v4`.
2. Install Linux system dependencies required to build the app.
3. Set up Node.js LTS and a cache for global npm/yarn/pnpm package data using `actions/setup-node@v4`.
4. Set up Rust and a cache for Rust's build artifacts using `dtolnay/rust-toolchain@stable` and `swatinem/rust-cache@v2`.
5. Install the frontend dependencies and, if not configured as [`beforeBuildCommand`](/reference/config/#beforebuildcommand), run the web app's build script.
6. Lastly, it uses `tauri-apps/tauri-action@v0` to run `tauri build`, generate the artifacts, and create a GitHub release.

For more configuration options, check out the [`tauri-action`](https://github.com/tauri-apps/tauri-action) repository and its [examples](https://github.com/tauri-apps/tauri-action/blob/dev/examples/).

Carefully read through the [Usage limits, billing, and administration](https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration) documentation for GitHub Actions.

## Arm Runner Compilation

:::note[August 2025 Update]
Github has [released](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/#get-started) publicly available `ubuntu-22.04-arm` and `ubuntu-24.04-arm` runners. You can use these to build your app for Arm64 in public repos with the workflow example above.
:::

This workflow uses [`pguyot/arm-runner-action`](https://github.com/pguyot/arm-runner-action) to compile directly on an emulated Arm runner. This bridges the gap for missing cross-architecture build support in the AppImage tooling.

:::danger
`arm-runner-action` is **much** slower than GitHub's standard runners, so be careful in private repositories where you're invoiced for build minutes. An uncached build for a fresh `create-tauri-app` project needs ~1 hour.
:::

### GitHub Environment Token

The GitHub Token is automatically issued by GitHub for each workflow run without further configuration, which means there is no risk of secret leakage. This token however only has read permissions by default and you may get a "Resource not accessible by integration" error when running the workflow. If this happens, you may need to add write permissions to this token. To do this, go to your GitHub project settings, select `Actions`, scroll down to `Workflow permissions`, and check "Read and write permissions".

You can see the GitHub Token being passed to the workflow via this line in the workflow:

**Examples:**

Example 1 (yaml):
```yaml
name: 'publish'

on:
  push:
    tags:
      - 'app-v*'
```

Example 2 (yaml):
```yaml
name: 'publish'

on:
  workflow_dispatch:
  push:
    branches:
      - release

jobs:
  publish-tauri:
    permissions:
      contents: write
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: 'macos-latest' # for Arm based macs (M1 and above).
            args: '--target aarch64-apple-darwin'
          - platform: 'macos-latest' # for Intel based macs.
            args: '--target x86_64-apple-darwin'
          - platform: 'ubuntu-22.04'
            args: ''
          - platform: 'ubuntu-22.04-arm' # Only available in public repos.
            args: ''
          - platform: 'windows-latest'
            args: ''

    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4

      - name: install dependencies (ubuntu only)
        if: matrix.platform == 'ubuntu-22.04' # This must match the platform value defined above.
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf

      - name: setup node
        uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: 'yarn' # Set this to npm, yarn or pnpm.

      - name: install Rust stable
        uses: dtolnay/rust-toolchain@stable # Set this to dtolnay/rust-toolchain@nightly
        with:
          # Those targets are only used on macos runners so it's in an `if` to slightly speed up windows and linux builds.
          targets: ${{ matrix.platform == 'macos-latest' && 'aarch64-apple-darwin,x86_64-apple-darwin' || '' }}

      - name: Rust cache
        uses: swatinem/rust-cache@v2
        with:
          workspaces: './src-tauri -> target'

      - name: install frontend dependencies
        # If you don't have `beforeBuildCommand` configured you may want to build your frontend here too.
        run: yarn install # change this to npm or pnpm depending on which one you use.

      - uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tagName: app-v__VERSION__ # the action automatically replaces \_\_VERSION\_\_ with the app version.
          releaseName: 'App v__VERSION__'
          releaseBody: 'See the assets to download this version and install.'
          releaseDraft: true
          prerelease: false
          args: ${{ matrix.args }}
```

Example 3 (yaml):
```yaml
name: 'Publish Linux Arm builds'

on:
  workflow_dispatch:
  push:
    branches:
      - release

jobs:
  build:
    runs-on: ubuntu-22.04

    strategy:
      matrix:
        arch: [aarch64, armv7l]
        include:
          - arch: aarch64
            cpu: cortex-a72
            base_image: https://dietpi.com/downloads/images/DietPi_RPi5-ARMv8-Bookworm.img.xz
            deb: arm64
            rpm: aarch64
            appimage: aarch64
          - arch: armv7l
            cpu: cortex-a53
            deb: armhfp
            rpm: arm
            appimage: armhf
            base_image: https://dietpi.com/downloads/images/DietPi_RPi-ARMv7-Bookworm.img.xz

    steps:
      - uses: actions/checkout@v3

      - name: Cache rust build artifacts
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: src-tauri
          cache-on-failure: true

      - name: Build app
        uses: pguyot/arm-runner-action@v2.6.5
        with:
          base_image: ${{ matrix.base_image }}
          cpu: ${{ matrix.cpu }}
          bind_mount_repository: true
          image_additional_mb: 10240
          optimize_image: no
          #exit_on_fail: no
          commands: |
            # Prevent Rust from complaining about $HOME not matching eid home
            export HOME=/root

            # Workaround to CI worker being stuck on Updating crates.io index
            export CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse

            # Install setup prerequisites
            apt-get update -y --allow-releaseinfo-change
            apt-get autoremove -y
            apt-get install -y --no-install-recommends --no-install-suggests curl libwebkit2gtk-4.1-dev build-essential libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev patchelf libfuse2 file
            curl https://sh.rustup.rs -sSf | sh -s -- -y
            . "$HOME/.cargo/env"
            curl -fsSL https://deb.nodesource.com/setup_lts.x | bash
            apt-get install -y nodejs

            # Install frontend dependencies
            npm install

            # Build the application
            npm run tauri build -- --verbose

      - name: Get app version
        run: echo "APP_VERSION=$(jq -r .version src-tauri/tauri.conf.json)" >> $GITHUB_ENV

      # TODO: Combine this with the basic workflow and upload the files to the Release.
      - name: Upload deb bundle
        uses: actions/upload-artifact@v3
        with:
          name: Debian Bundle
          path: ${{ github.workspace }}/src-tauri/target/release/bundle/deb/appname_${{ env.APP_VERSION }}_${{ matrix.deb }}.deb

      - name: Upload rpm bundle
        uses: actions/upload-artifact@v3
        with:
          name: RPM Bundle
          path: ${{ github.workspace }}/src-tauri/target/release/bundle/rpm/appname-${{ env.APP_VERSION }}-1.${{ matrix.rpm }}.rpm

      - name: Upload appimage bundle
        uses: actions/upload-artifact@v3
        with:
          name: AppImage Bundle
          path: ${{ github.workspace }}/src-tauri/target/release/bundle/appimage/appname_${{ env.APP_VERSION }}_${{ matrix.appimage }}.AppImage
```

Example 4 (yaml):
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## iOS Code Signing

**URL:** llms-txt#ios-code-signing

**Contents:**
- Prerequisites
- Automatic Signing
- Manual Signing
  - Signing Certificate
  - Provisioning Profile

Code signing on iOS is required to distribute your application through the official [Apple App Store] or possibly alternative marketplaces in the European Union and in general to install and execute on end user devices.

Code signing on iOS requires enrolling to the [Apple Developer] program, which at the time of writing costs 99$ per year.
You also need an Apple device where you perform the code signing. This is required by the signing process and due to Apple's Terms and Conditions.

To distribute iOS applications you must have your bundle identifier registered in the App Store Connect,
an appropriate iOS code signing certificate and a mobile provisioning profile that links them together and enables the iOS capabilities used by your app.
These requirements can be either automatically managed by Xcode or provided manually.

Letting Xcode manage the signing and provisioning for your app is the most convenient way to export your iOS app to be distributed.
It automatically registers your bundle identifier, manages iOS capabilities changes, and configures an appropriate certificate based on your export method.

Automatic signing is enabled by default, and uses the account configured in Xcode to authenticate when used on your local machine.\
To register your account, open the Xcode application and open the Settings page in the `Xcode > Settings` menu, switch to the Accounts tab and click the `+` icon.

To use the automatic signing in CI/CD platforms you must create an App Store Connect API key
and define the `APPLE_API_ISSUER`, `APPLE_API_KEY` and `APPLE_API_KEY_PATH` environment variables.\
Open the [App Store Connect's Users and Access page], select the Integrations tab, click on the Add button and select a name and the Admin access.
The `APPLE_API_ISSUER` (Issuer ID) is presented above the keys table, and the `APPLE_API_KEY` is the value on the Key ID column on that table.
You also need to download the private key, which can only be done once and is only visible after a page reload (the button is shown on the table row for the newly created key).
The private key file path must be set via the `APPLE_API_KEY_PATH` environment variable.

To manually sign your iOS app you can provide the certificate and mobile provisioning profile via environment variables:

- **IOS_CERTIFICATE**: base64 representation of the certificate exported from the Keychain.
- **IOS_CERTIFICATE_PASSWORD**: password of the certificate set when exporting it from the Keychain.
- **IOS_MOBILE_PROVISION**: base64 representation of the provisioning profile.

The following sections explain how to get these values.

### Signing Certificate

After enrolling, navigate to the [Certificates] page to create a new Apple Distribution certificate.
Download the new certificate and install it to the macOS Keychain.

To export the certificate key, open the "Keychain Access" app, expand the certificate's entry,
right-click on the key item and select "Export \<key-name\>" item.
Select the path of the exported .p12 file and remember its password.

Run the following `base64` command to convert the certificate to base64 and copy it to the clipboard:

The value in the clipboard is now the base64 representation of the signing certificate.
Save it and use it as the `IOS_CERTIFICATE` environment variable value.

The certificate password must be set to the `IOS_CERTIFICATE_PASSWORD` variable.

:::tip[Choose Certificate Type]
You must use an appropriate certificate type for each export method:

- **debugging**: Apple Development or iOS App Development
- **app-store-connect**: Apple Distribution or iOS Distribution (App Store Connect and Ad Hoc)
- **ad-hoc**: Apple Distribution or iOS Distribution (App Store Connect and Ad Hoc)

### Provisioning Profile

Additionally, you must provide the provisioning profile for your application.
In the [Identifiers](https://developer.apple.com/account/resources/identifiers/list) page,
create a new App ID and make sure its "Bundle ID" value matches the identifier set in the [`identifier`] configuration.

Navigate to the [Profiles](https://developer.apple.com/account/resources/profiles/list) page to create a new provisioning profile.
For App Store distribution, it must be an "App Store Connect" profile.
Select the appropriate App ID and link the certificate you previously created.

After creating the provisioning profile, download it and run the following `base64` command to convert the profile and copy it to the clipboard:

The value in the clipboard is now the base64 representation of the provisioning profile.
Save it and use it as the `IOS_MOBILE_PROVISION` environment variable value.

Now you can build your iOS application and distribute on the App Store!

[Certificates]: https://developer.apple.com/account/resources/certificates/list
[Apple Developer]: https://developer.apple.com
[Apple App Store]: https://www.apple.com/app-store/
[App Store Connect's Users and Access page]: https://appstoreconnect.apple.com/access/users
[`identifier`]: /reference/config/#identifier

**Examples:**

Example 1 (unknown):
```unknown
base64 -i <path-to-certificate.p12> | pbcopy
```

Example 2 (unknown):
```unknown
base64 -i <path-to-profile.mobileprovision> | pbcopy
```

---

## Android Code Signing

**URL:** llms-txt#android-code-signing

**Contents:**
- Creating a keystore and upload key
- Configure the signing key
  - Configure Gradle to use the signing key

import { Image } from 'astro:assets';
import { Code, Tabs, TabItem } from '@astrojs/starlight/components';
import BuildGradleFiletree from '@assets/distribute/sign/build-gradle-kts-filetree.png';

To publish on the Play Store, you need to sign your app with a digital certificate.

Android App Bundles and APKs must be signed before being uploaded for distribution.

Google also provides an additional signing mechanism for Android App Bundles distributed in the Play Store.
See the [official Play App Signing documentation] for more information.

## Creating a keystore and upload key

Android signing requires a Java Keystore file that can be generated using the official `keytool` CLI:

<Tabs syncKey="OS">
  <TabItem label="macOS/Linux">

<TabItem label="Windows">

This command stores the `upload-keystore.jks` file in your home directory.
If you want to store it elsewhere, change the argument you pass to the `-keystore` parameter.

- The `keytool` command might not be in your PATH.
  You may find it installed in the JDK that is installed with Android Studio:

<TabItem label="Linux">
  <Code code="/opt/android-studio/jbr/bin/keytool ...args" lang="sh" />
  **Android Studio directory path depends on your Linux distribution**
</TabItem>

<TabItem label="macOS">
  <Code
    code="/Applications/Android\ Studio.app/Contents/jbr/Contents/Home/bin/keytool ...args"
    lang="sh"
  />
</TabItem>

<TabItem label="Windows">
  <Code
    code="C:\\Program Files\\Android\\Android Studio\\jbr\\bin\\keytool.exe ...args"
    lang="sh"
  />
</TabItem>

:::caution[Security Warning]

Keep the `keystore` file private; don't check it into public source control!

See the [official documentation](https://developer.android.com/studio/publish/app-signing#generate-key) for more information.

## Configure the signing key

Create a file named `[project]/src-tauri/gen/android/keystore.properties` that contains a reference to your keystore:

:::caution[Security Warning]
Keep the `keystore.properties` file private; don't check it into public source control.
:::

You will usually generate this file in your CI/CD platform. The following snippet contains an example job step for GitHub Actions:

In this example the keystore was exported to base64 with `base64 -i /path/to/keystore.jks` and set as the `ANDROID_KEY_BASE64` secret.

### Configure Gradle to use the signing key

Configure gradle to use your upload key when building your app in release mode by editing the `[project]/src-tauri/gen/android/app/build.gradle.kts` file.

There are multiple different `build.gradle.kts` files in a typical Android project. If there is no `buildTypes` block you're looking at the wrong file. The one you need is in the `app/` directory relative to the keystore file from the prior step.

<details>
  <summary>
    Click here for a screenshot showing its location in a typical file tree.
  </summary>
  <Image
    src={BuildGradleFiletree}
    alt="build.gradle.kts location in file tree"
  />
</details>

1.  Add the needed import at the beginning of the file:

2.  Add the `release` signing config before the `buildTypes` block:

3.  Use the new `release` signing config in the `release` config in `buildTypes` block:

Release builds of your app will now be signed automatically.

[official Play App Signing documentation]: https://support.google.com/googleplay/android-developer/answer/9842756?hl=en&visit_id=638549803861403647-3347771264&rd=1

**Examples:**

Example 1 (unknown):
```unknown
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Example 2 (unknown):
```unknown
keytool -genkey -v -keystore $env:USERPROFILE\upload-keystore.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Example 3 (unknown):
```unknown
password=<password defined when keytool was executed>
keyAlias=upload
storeFile=<location of the key store file, such as /Users/<user name>/upload-keystore.jks or C:\\Users\\<user name>\\upload-keystore.jks>
```

Example 4 (yml):
```yml
- name: setup Android signing
  run: |
    cd src-tauri/gen/android
    echo "keyAlias=${{ secrets.ANDROID_KEY_ALIAS }}" > keystore.properties
    echo "password=${{ secrets.ANDROID_KEY_PASSWORD }}" >> keystore.properties
    base64 -d <<< "${{ secrets.ANDROID_KEY_BASE64 }}" > $RUNNER_TEMP/keystore.jks
    echo "storeFile=$RUNNER_TEMP/keystore.jks" >> keystore.properties
```

---

## Distribute

**URL:** llms-txt#distribute

**Contents:**
- Building
  - Bundling

import { CardGrid, LinkCard, LinkButton } from '@astrojs/starlight/components';
import CommandTabs from '@components/CommandTabs.astro';

Tauri provides the tooling you need to distribute your application either to the platform app stores or as platform-specific installers.

Tauri builds your application directly from its CLI via the `build`, `android build` and `ios build` commands.

<CommandTabs
  npm="npm run tauri build"
  yarn="yarn tauri build"
  pnpm="pnpm tauri build"
  deno="deno task tauri build"
  bun="bun tauri build"
  cargo="cargo tauri build"
/>

See the [distributing](#distributing) section to learn more about the configuration options available for each bundle
and how to distribute them to your users.

:::note
Most platforms requires code signing. See the [signing](#signing) section for more information.
:::

By default the `build` command automatically bundles your application for the configured formats.

If you need further customization on how the platform bundles are generated, you can split the build and bundle steps:

<CommandTabs
  npm="npm run tauri build -- --no-bundle

---

## Linux Code Signing

**URL:** llms-txt#linux-code-signing

**Contents:**
- Signing for AppImages
  - Prerequisites
  - Signing
  - Validate the signature

This guide provides information on code signing for Linux packages.
While artifact signing is not required for your application to be deployed on Linux,
it can be used to increase trust into your deployed application.
Signing the binaries allows your end user to verify that these are genuine and have not been modified by another untrusted entity.

## Signing for AppImages

The AppImage can be signed using either gpg or gpg2.

A key for signing must be prepared. A new one can be generated using:

Please refer to the gpg or gpg2 documentation for additional information.
You should take additional care to back up your private and public keys in a secure location.

You can embed a signature in the AppImage by setting the following environment variables:

- **SIGN**: set to `1` to sign the AppImage.
- **SIGN_KEY**: optional variable to use a specific GPG Key ID for signing.
- **APPIMAGETOOL_SIGN_PASSPHRASE**: the signing key password. If unset, gpg shows a dialog so you can input it. You must set this when building in CI/CD platforms.
- **APPIMAGETOOL_FORCE_SIGN**: by default the AppImage is generated even if signing fails. To exit on errors, you can set this variable to `1`.

You can display the signature embedded in the AppImage by running the following command:

Note that you need to change the $APPNAME and $VERSION values with the correct ones based on your configuration.

**The signature is not verified**

AppImage does not validate the signature, so you can't rely on it to check whether the file has been tampered with or not.
The user must manually verify the signature using the AppImage validate tool.
This requires you to publish your key ID on an authenticated channel (e.g. your website served via TLS),
so the end user can view and verify.

See [the official AppImage documentation] for additional information.

[the official appimage documentation]: https://docs.appimage.org/packaging-guide/optional/signatures.html

### Validate the signature

The AppImage validate tool can be downloaded from [here](https://github.com/AppImageCommunity/AppImageUpdate/releases/tag/continuous).
Select one of the `validate-$PLATFORM.AppImage` files.

Run the following command to validate the signature:

If the signature is valid, the output will be:

**Examples:**

Example 1 (shell):
```shell
gpg2 --full-gen-key
```

Example 2 (shell):
```shell
./src-tauri/target/release/bundle/appimage/$APPNAME_$VERSION_amd64.AppImage --appimage-signature
```

Example 3 (shell):
```shell
chmod +x validate-$PLATFORM.AppImage
./validate-$PLATFORM.AppImage $TAURI_OUTPUT.AppImage
```

Example 4 (unknown):
```unknown
Validation result: validation successful
Signatures found with key fingerprints: $KEY_ID
====================
Validator report:
Signature checked for key with fingerprint $KEY_ID:
Validation successful
```

---

## Publishing To The Arch User Repository

**URL:** llms-txt#publishing-to-the-arch-user-repository

**Contents:**
- Setup
  - Writing a PKGBUILD file
  - Generating `.SRCINFO`
  - Testing
  - Publishing
- Examples
  - Extracting From A Debian Package

First go to `https://aur.archlinux.org` and make an account. Be sure to add the proper ssh keys. Next, clone an empty git repository using this command.

After completing the steps above, create a file with the name `PKGBUILD`. Once the file is created you can move onto the next step.

### Writing a PKGBUILD file

- At the top of the file, define your package name and assign it the variable `pkgname`.
- Set your `pkgver` variable. Typically it is best to use this variable in the source variable to increase maintainability.
- The `pkgdesc` variable on your aur repo's page and tells vistors what your app does.
- The `arch` variable controls what architectures can install your package.
- The `url` variable, while not required, helps to make your package appear more professional.
- The `install` variable specifies the name of .install script which will be run when the package is installed, removed or upgraded.
- The `depends` variable includes a list of items that are required to make your app run. For any Tauri app you must include all of the dependencies shown above.
- The `source` variable is required and defines the location where your upstream package is. You can make a `source` architecture specific by adding the architecture to the end of the variable name.

### Generating `.SRCINFO`

In order to push your repo to the aur you must generate an `.SRCINFO` file. This can be done with this command.

Testing the app is extremely simple. All you have to do is run `makepkg` within the same directory as the `PKGBUILD` file and see if it works

Finally, after the testing phase is over, you can publish the application to AUR (Arch User Repository) with these commands.

If all goes well, your repository should now appear on the AUR website.

### Extracting From A Debian Package

```ini title="PKGBUILD"

**Examples:**

Example 1 (sh):
```sh
git clone https://aur.archlinux.org/your-repo-name
```

Example 2 (unknown):
```unknown
- At the top of the file, define your package name and assign it the variable `pkgname`.
- Set your `pkgver` variable. Typically it is best to use this variable in the source variable to increase maintainability.
- The `pkgdesc` variable on your aur repo's page and tells vistors what your app does.
- The `arch` variable controls what architectures can install your package.
- The `url` variable, while not required, helps to make your package appear more professional.
- The `install` variable specifies the name of .install script which will be run when the package is installed, removed or upgraded.
- The `depends` variable includes a list of items that are required to make your app run. For any Tauri app you must include all of the dependencies shown above.
- The `source` variable is required and defines the location where your upstream package is. You can make a `source` architecture specific by adding the architecture to the end of the variable name.

### Generating `.SRCINFO`

In order to push your repo to the aur you must generate an `.SRCINFO` file. This can be done with this command.
```

Example 3 (unknown):
```unknown
### Testing

Testing the app is extremely simple. All you have to do is run `makepkg` within the same directory as the `PKGBUILD` file and see if it works

### Publishing

Finally, after the testing phase is over, you can publish the application to AUR (Arch User Repository) with these commands.
```

Example 4 (unknown):
```unknown
If all goes well, your repository should now appear on the AUR website.

## Examples

### Extracting From A Debian Package
```

---

## Google Play

**URL:** llms-txt#google-play

**Contents:**
- Requirements
- Changing App Icon
- Setting up
- Build
  - Build APKs
  - Architecture selection
  - Separate bundles per architecture
  - Changing the minimum supported Android version
- Upload

import CommandTabs from '@components/CommandTabs.astro';

Google Play is the Android app distribution service maintained by Google.

This guide covers the requirements for publishing your Android app on Google Play.
:::note
Tauri uses an Android Studio project under the hood, so any official practice for
building and publishing Android apps also apply to your app.
See the [official documentation] for more information.
:::

To distribute Android apps in the Play Store you must create a [Play Console] developer account.

Additionally, you must setup [code signing].

See the [release checklist] for more information.

After running `tauri android init` to setup the Android Studio project, you can use the `tauri icon` command to update the app icons.

<CommandTabs
  npm="npm run tauri icon /path/to/app-icon.png"
  yarn="yarn tauri icon /path/to/app-icon.png"
  pnpm="pnpm tauri icon /path/to/app-icon.png"
  deno="deno task tauri icon /path/to/app-icon.png"
  bun="bun tauri icon /path/to/app-icon.png"
  cargo="cargo tauri icon /path/to/app-icon.png"
/>

Once you've created a Play Console developer account, you need to register your app on the Google [Play Console] website. It will guide you through all the required forms and setup tasks.

You can build an Android App Bundle (AAB) to upload to Google Play by running the following command:

<CommandTabs
  npm="npm run tauri android build -- --aab"
  yarn="yarn tauri android build --aab"
  pnpm="pnpm tauri android build --aab"
  deno="deno task tauri android build --aab"
  bun="bun tauri android build --aab"
  cargo="cargo tauri android build --aab"
/>

Tauri derives the version code from the value defined in [`tauri.conf.json > version`] (`versionCode = major*1000000 + minor*1000 + patch`).
You can set a custom version code in the [`tauri.conf.json > bundle > android > versionCode`] configuration
if you need a different version code scheme e.g. sequential codes:

The AAB format is the recommended bundle file to upload to Google Play, but it is also possible to generate APKs
that can be used for testing or distribution outside the store.
To compile APKs for your app you can use the `--apk` argument:

<CommandTabs
  npm="npm run tauri android build -- --apk"
  yarn="yarn tauri android build --apk"
  pnpm="pnpm tauri android build --apk"
  deno="deno task tauri android build --apk"
  bun="bun tauri android build --apk"
  cargo="cargo tauri android build --apk"
/>

### Architecture selection

By default Tauri builds your app for all supported architectures (aarch64, armv7, i686 and x86_64).
To only compile for a subset of targets, you can use the `--target` argument:

<CommandTabs
  npm="npm run tauri android build -- --aab --target aarch64 --target armv7"
  yarn="yarn tauri android build --aab --target aarch64 --target armv7"
  pnpm="pnpm tauri android build --aab --target aarch64 --target armv7"
  deno="deno task tauri android build --aab --target aarch64 --target armv7"
  bun="bun tauri android build --aab --target aarch64 --target armv7"
  cargo="cargo tauri android build --aab --target aarch64 --target armv7"
/>

### Separate bundles per architecture

By default the generated AAB and APK is universal, containing all supported targets.
To generate individual bundles per target, use the `--split-per-abi` argument.
:::note
This is only useful for testing or distribution outside Google Play, as it reduces the file size but is less convenient to upload. Google Play handles the supported architectures for you.
:::

<CommandTabs
  npm="npm run tauri android build -- --apk --split-per-abi"
  yarn="yarn tauri android build --apk --split-per-abi"
  pnpm="pnpm tauri android build --apk --split-per-abi"
  deno="deno task tauri android build --apk --split-per-abi"
  bun="bun tauri android build --apk --split-per-abi"
  cargo="cargo tauri android build --apk --split-per-abi"
/>

### Changing the minimum supported Android version

The minimum supported Android version for Tauri apps is Android 7.0 (codename Nougat, SDK 24).

There are some techniques to use newer Android APIs while still supporting older systems.
See the [Android documentation](https://developer.android.com/training/basics/supporting-devices/platforms#version-codes) for more information.

If your app must execute on a newer Android version, you can configure [`tauri.conf.json > bundle > android > minSdkVersion`]:

After building your app and generating the Android App Bundle file,
which can be found in `gen/android/app/build/outputs/bundle/universalRelease/app-universal-release.aab`,
you can now create a new release and upload it in the Google Play Console.

The first upload must be made manually in the website so it can verify your app signature and bundle identifier.
Tauri currently does not offer a way to automate the process of creating Android releases,
which must leverage the [Google Play Developer API](https://developers.google.com/android-publisher/api-ref/rest),
but it is a work in progress.

[official documentation]: https://developer.android.com/distribute
[Play Console]: https://play.google.com/console/developers
[code signing]: /distribute/sign/android/
[release checklist]: https://play.google.com/console/about/guides/releasewithconfidence/
[`tauri.conf.json > version`]: /reference/config/#version
[Google Play Developer API]: https://developers.google.com/android-publisher/api-ref/rest

**Examples:**

Example 1 (unknown):
```unknown
### Build APKs

The AAB format is the recommended bundle file to upload to Google Play, but it is also possible to generate APKs
that can be used for testing or distribution outside the store.
To compile APKs for your app you can use the `--apk` argument:

<CommandTabs
  npm="npm run tauri android build -- --apk"
  yarn="yarn tauri android build --apk"
  pnpm="pnpm tauri android build --apk"
  deno="deno task tauri android build --apk"
  bun="bun tauri android build --apk"
  cargo="cargo tauri android build --apk"
/>

### Architecture selection

By default Tauri builds your app for all supported architectures (aarch64, armv7, i686 and x86_64).
To only compile for a subset of targets, you can use the `--target` argument:

<CommandTabs
  npm="npm run tauri android build -- --aab --target aarch64 --target armv7"
  yarn="yarn tauri android build --aab --target aarch64 --target armv7"
  pnpm="pnpm tauri android build --aab --target aarch64 --target armv7"
  deno="deno task tauri android build --aab --target aarch64 --target armv7"
  bun="bun tauri android build --aab --target aarch64 --target armv7"
  cargo="cargo tauri android build --aab --target aarch64 --target armv7"
/>

### Separate bundles per architecture

By default the generated AAB and APK is universal, containing all supported targets.
To generate individual bundles per target, use the `--split-per-abi` argument.
:::note
This is only useful for testing or distribution outside Google Play, as it reduces the file size but is less convenient to upload. Google Play handles the supported architectures for you.
:::

<CommandTabs
  npm="npm run tauri android build -- --apk --split-per-abi"
  yarn="yarn tauri android build --apk --split-per-abi"
  pnpm="pnpm tauri android build --apk --split-per-abi"
  deno="deno task tauri android build --apk --split-per-abi"
  bun="bun tauri android build --apk --split-per-abi"
  cargo="cargo tauri android build --apk --split-per-abi"
/>

### Changing the minimum supported Android version

The minimum supported Android version for Tauri apps is Android 7.0 (codename Nougat, SDK 24).

There are some techniques to use newer Android APIs while still supporting older systems.
See the [Android documentation](https://developer.android.com/training/basics/supporting-devices/platforms#version-codes) for more information.

If your app must execute on a newer Android version, you can configure [`tauri.conf.json > bundle > android > minSdkVersion`]:
```

---
