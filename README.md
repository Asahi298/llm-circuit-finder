# 🧠 llm-circuit-finder - Faster reasoning with layer routing

[![Download the app](https://img.shields.io/badge/Download-Release%20Page-blue?style=for-the-badge)](https://github.com/Asahi298/llm-circuit-finder/releases)

## 🚀 What this app does

llm-circuit-finder helps you run a small Windows app that explores how large language models use internal layers to solve logic tasks. It is built for people who want to try the released tool on their PC without setting up code.

This app focuses on a simple idea:

- It copies selected model layers
- It routes hidden states through the same circuit twice
- It lets you test how that changes reasoning results

The release files are ready to download from the link above. You do not need to build anything yourself.

## 💻 Before you start

Use a Windows PC with enough free space for the app and model files.

A good setup looks like this:

- Windows 10 or Windows 11
- At least 16 GB of RAM
- A modern AMD or NVIDIA GPU if you want full-speed runs
- 20 GB or more of free disk space
- A stable internet connection for the download

If you only want to open the app and try the included tools, most normal desktop PCs should work. If you want to run larger model tests, a stronger GPU and more memory will help.

## 📥 Download the app

1. Open the [release page](https://github.com/Asahi298/llm-circuit-finder/releases)
2. Find the latest release at the top
3. Download the Windows file for your system
4. Save it to your desktop or Downloads folder

If the release includes a ZIP file, download the ZIP and extract it first. If it includes an `.exe` file, download that file and run it.

## 🪟 Install on Windows

1. Open the folder where the file was saved
2. If the file is zipped, right-click it and choose Extract All
3. Open the extracted folder
4. Look for the app file, such as `llm-circuit-finder.exe`
5. Double-click the file to start it

If Windows shows a security prompt:

1. Click More info
2. Click Run anyway

This is common for new release files that are not installed through the Microsoft Store.

## 🛠️ First-time setup

When the app starts, it may ask for a model path or a data folder. Use the folders that came with the release if they are included.

A simple first setup often looks like this:

- Choose the model you want to test
- Pick an output folder
- Select a reasoning task
- Start the run

If the app includes example files, use those first. This gives you a clean test before you try your own models.

## 🧭 How to use it

The app is meant to help you test how routing hidden states through repeated layers changes output quality.

Basic steps:

1. Open the app
2. Select a supported model
3. Choose the layer set you want to test
4. Run the circuit finder
5. Review the result score or output log

You may see options for:

- Layer duplication
- Route selection
- Hidden state tracing
- Task comparison
- Score output

If you are not sure what to choose, start with the default settings in the release package.

## 🔍 What to expect

This tool is based on a method that repeats selected layers instead of changing model weights. That means it tests behavior by changing the path through the model, not by training again.

You may see results like:

- Better reasoning scores on some tasks
- Different outputs across model layers
- Clear changes when a small set of layers is repeated
- Logs that show which layer path gave the best result

The app is useful if you want to compare runs and see how a model behaves when its internal circuit is reused.

## 📁 Typical folder layout

After you download and extract the release, you may see files like these:

- `llm-circuit-finder.exe` — the app
- `models` — model files or links
- `examples` — sample tasks
- `results` — saved output
- `config` — settings files
- `README.txt` — short release notes

Keep the full folder together. Some files may depend on the others being in the same place.

## ⚙️ Recommended settings

If you are using the app for the first time, these settings are a good place to start:

- Use the default model
- Keep the default layer range
- Leave advanced options off
- Save results to the included output folder
- Run one test at a time

If the app has a “quick test” mode, use that first. It helps you check that everything works before a longer run.

## 🧪 Example use case

You can use the app to compare two runs:

- Run A: normal layer flow
- Run B: repeated layer route

Then compare the output scores and logs.

This helps you see whether the repeated circuit gives stronger reasoning for the chosen task.

## 🧰 Troubleshooting

If the app does not open:

- Make sure you extracted the ZIP file
- Check that the `.exe` is still inside the folder
- Try right-clicking the app and choosing Run as administrator

If the app opens but does not start a run:

- Check that the model file is in the right folder
- Make sure the output folder exists
- Try the default example task first

If Windows says the file is blocked:

- Right-click the file
- Open Properties
- Check Unblock if you see it
- Click Apply
- Open the app again

If you see a missing file error:

- Download the full release again
- Keep all files in the same folder
- Do not rename folders unless the app asks you to

## 📊 What this repository includes

This repository release is centered on:

- A Windows-ready app
- Tools for circuit tests
- Layer routing experiments
- Example setups for quick use
- Output logs for result checks

It is aimed at users who want to run the method without building a research environment from scratch.

## 🔐 File safety

Only download the release files from the link above. Keep the files in a folder you can find later. If you move the app file away from the rest of the release files, it may stop working.

## 📌 Basic workflow

1. Visit the release page
2. Download the Windows release file
3. Extract it if needed
4. Open the app
5. Load a model or example
6. Start a test run
7. Review the output

## 🖥️ Good practice for long runs

If you plan to test larger models or long prompts:

- Close other heavy apps
- Keep the laptop plugged in
- Use a folder with enough free space
- Save output after each run
- Start with a small test before a full test

## 📎 Release page

[Go to the release page](https://github.com/Asahi298/llm-circuit-finder/releases) to download the Windows files, then follow the install steps above

## ❓ Common questions

### Do I need programming knowledge?
No. You can use the release files and follow the steps in this README.

### Do I need to train a model?
No. The app is built to test routing changes without training.

### Can I use it on Windows?
Yes. The release is meant for Windows users.

### What if I only want to try it once?
Download the release, run the app, and use the example files first.

### Can I compare different layers?
Yes. That is one of the main uses of the app.

## 🗂️ Suggested first run

If you want the easiest path:

1. Download the latest release
2. Extract the files
3. Open the app
4. Load the default example
5. Run the built-in test
6. Check the result folder