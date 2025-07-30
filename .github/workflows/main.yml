name: Watch Face Generator with Auto-Cleanup and Preview Fix

on:
  repository_dispatch:
    types: [generate_watchface]
  workflow_dispatch:
    inputs:
      input_json:
        description: 'JSON containing model path and image Base64'
        required: true

jobs:
  generate:
    runs-on: windows-latest
    permissions:
      contents: write
      
    steps:
      # 1. Checkout code
      - name: Checkout repository
        uses: actions/checkout@v4

      # 2. Increase virtual memory
      - name: Increase virtual memory to 16GB
        run: |
          wmic computersystem set AutomaticManagedPagefile=False
          wmic pagefileset create name="C:\pagefile.sys"
          wmic pagefileset where name="C:\pagefile.sys" set InitialSize=16384,MaximumSize=16384
          wmic pagefileset list brief
          echo "Virtual memory increased to 16GB"

      # 3. Process input data
      - name: Parse input JSON
        id: parse-input
        run: |
          $inputData = if ('${{ github.event_name }}' -eq 'repository_dispatch') {
            '${{ toJson(github.event.client_payload.input_json) }}'
          } else {
            '${{ toJson(github.event.inputs.input_json) }}'
          }
          
          $jsonInput = $inputData | ConvertFrom-Json
          $jsonInput.model | Out-File "$env:RUNNER_TEMP\model_path.txt"
          $jsonInput.file | Out-File "$env:RUNNER_TEMP\image_base64.txt" -NoNewline
          
          echo "model_path_file=$env:RUNNER_TEMP\model_path.txt" >> $env:GITHUB_OUTPUT
          echo "base64_file=$env:RUNNER_TEMP\image_base64.txt" >> $env:GITHUB_OUTPUT

      # 4. Prepare project files
      - name: Prepare project directory
        id: prepare-project
        run: |
          # 设置项目目录路径
          $projectDir = "project"
          $fprjFile = "fprj.fprj"
          
          # 复制模型到项目目录
          $modelPath = Get-Content "$env:RUNNER_TEMP\model_path.txt"
          New-Item -Type Directory -Path $projectDir -Force
          Copy-Item "$(Split-Path $modelPath -Parent)\*" $projectDir -Recurse
          
          # 重命名FPRJ文件
          $fprjOriginal = Get-ChildItem $projectDir -Filter "*.fprj" | Select-Object -First 1
          if ($fprjOriginal) {
              Rename-Item $fprjOriginal.FullName (Join-Path $projectDir $fprjFile) -Force
          } else {
              Write-Error "No FPRJ file found"
              exit 1
          }
          
          # 保存Base64图片到项目目录
          $bytes = [Convert]::FromBase64String((Get-Content "${{ steps.parse-input.outputs.base64_file }}" -Raw))
          $watchfacePicPath = Join-Path $projectDir "pic.png"
          [IO.File]::WriteAllBytes($watchfacePicPath, $bytes)
          
          # 同时复制一份作为预览图（pre.png）
          $previewPath = Join-Path $projectDir "pre.png"
          Copy-Item $watchfacePicPath $previewPath -Force
          
          # 创建输出目录
          New-Item -Type Directory -Path "$projectDir\output" -Force
          
          # 记录项目路径
          echo "project_path=$projectDir" >> $env:GITHUB_OUTPUT
          echo "fprj_path=$(Join-Path $projectDir $fprjFile)" >> $env:GITHUB_OUTPUT
          echo "preview_path=$previewPath" >> $env:GITHUB_OUTPUT

      # 5. Set up Python with Pillow
      - name: Set up Python 3.10 and Pillow
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install Pillow for image resizing
        run: pip install Pillow

      # 6. Run compilation script with error handling
      - name: Compile Watch Face (with retry)
        id: compile-watchface
        env:
          PROJECT_PATH: "${{ steps.prepare-project.outputs.fprj_path }}"
          OUTPUT_DIR: "${{ github.workspace }}/output"
        run: |
          # 错误处理函数
          function Handle-PreviewError {
            param($errorOutput)
            
            # 检查是否是预览尺寸错误
            if ($errorOutput -match 'Preview has wrong size: (\d+)x(\d+), expected: (\d+)x(\d+)') {
              $expectedWidth = $Matches[3]
              $expectedHeight = $Matches[4]
              
              # 获取预览图路径
              $previewPath = "${{ steps.prepare-project.outputs.preview_path }}"
              
              # 使用Python调整图片尺寸
              python -c "`
                from PIL import Image; `
                img = Image.open(r'$previewPath'); `
                img = img.resize(($expectedWidth, $expectedHeight)); `
                img.save(r'$previewPath'); `
                print(f'Resized preview to {expectedWidth}x{expectedHeight}')"
                
              return $true
            }
            return $false
          }
          
          # 首次尝试编译
          echo "First compilation attempt..."
          python compile_watchface.py 2>&1 | Tee-Object -Variable output
          if ($LASTEXITCODE -eq 0) {
            echo "Compilation succeeded on first attempt"
            exit 0
          }
          
          # 尝试处理预览尺寸错误
          if (Handle-PreviewError $output) {
            # 重新编译
            echo "Retrying compilation after resizing preview..."
            python compile_watchface.py
            if ($LASTEXITCODE -eq 0) {
              echo "Compilation succeeded after preview fix"
              exit 0
            } else {
              # 第二次编译失败
              echo "Compilation failed even after preview fix"
              exit 1
            }
          }
          
          # 无法识别的错误类型
          echo "Compilation failed for unknown reasons"
          exit 1

      # 7. Verify output
      - name: Verify Output File
        id: verify-output
        run: |
          $outputDir = "${{ github.workspace }}/output"
          $file = Get-ChildItem $outputDir -Filter "*.face"
          if ($file) {
              echo "face_file=$($file.FullName)" >> $env:GITHUB_OUTPUT
          } else {
              Write-Error "Output file not found"
              exit 1
          }

      # 8. Create Release
      - name: Create Release
        id: create-release
        uses: softprops/action-gh-release@v2
        env:
          GITHUB_TOKEN: ${{ secrets.PAT }}
        with:
          tag_name: "face-${{ github.run_id }}"
          files: ${{ steps.verify-output.outputs.face_file }}
          draft: false
          prerelease: false

      # 9. Pass release data
      - name: Store Release Data
        id: pass-data
        run: |
          echo "release_id=${{ steps.create-release.outputs.id }}" >> $env:GITHUB_OUTPUT
          echo "release_tag=face-${{ github.run_id }}" >> $env:GITHUB_OUTPUT

    outputs:
      release_id: ${{ steps.pass-data.outputs.release_id }}
      release_tag: ${{ steps.pass-data.outputs.release_tag }}

  delete_release:
    name: Auto-Delete Release
    needs: generate
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      # 1. Wait 10 minutes (using native sleep)
      - name: Wait for 10 minutes
        run: sleep 600
      
      # 2. Delete release and tag
      - name: Delete Release Assets
        uses: actions/github-script@v6
        env:
          GITHUB_TOKEN: ${{ secrets.PAT }}
        with:
          script: |
            const { release_id, release_tag } = {
              release_id: ${{ needs.generate.outputs.release_id }},
              release_tag: '${{ needs.generate.outputs.release_tag }}'
            };
            
            if (!release_id || !release_tag) {
              core.setFailed('Missing release information');
              return;
            }
            
            try {
              // Delete release
              await github.rest.repos.deleteRelease({
                owner: context.repo.owner,
                repo: context.repo.repo,
                release_id: release_id
              });
              
              // Delete tag
              await github.rest.git.deleteRef({
                owner: context.repo.owner,
                repo: context.repo.repo,
                ref: `tags/${release_tag}`
              });
              
              core.info(`Successfully deleted release ${release_id} and tag ${release_tag}`);
            } catch (error) {
              if (error.status === 404) {
                core.warning('Release or tag not found (may have been already deleted)');
              } else {
                core.setFailed(`Deletion failed: ${error.message}`);
              }
            }
