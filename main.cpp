#include <fstream>
#include <iostream>
#include <string>
#include <cstdlib>
#include <filesystem>
#include "json.hpp"
using json = nlohmann::json;
namespace  fs = std::filesystem;

const std::string launcher_json_file_name = "launcher.json";

std::string ACTIVATED = "false";
std::string LATEX_INSTALLED = "false";

void exit_and_wait(const int code) {
    system("pause");
    exit(code);
}

void write_to_file() {
    json data;
    data["activated"] = ACTIVATED;
    data["latex_installed"] = LATEX_INSTALLED;

    std::ofstream ofs(launcher_json_file_name);
    if (ofs.is_open()) {
        ofs<<data.dump(4);
        ofs.close();
    }else {
        std::cerr<<"无法创建launcher.json文件"<<std::endl;
        exit_and_wait(1);
    }
}

void run_failed() {
    ACTIVATED = "false";
    LATEX_INSTALLED = "false";
    write_to_file();
    std::cerr<<"请重新启动程序"<<std::endl;
    exit_and_wait(1);
}

void activate() {
    std::cout<<"首次启动，正在配置环境..."<<std::endl;
    if (!fs::exists("scripts\\init_venv.bat")) {
        std::cerr << "未找到配置环境脚本" << std::endl;
        run_failed();
    }
    int exit_code = system("scripts\\init_venv.bat");
    if (exit_code == 0) {
        std::cout << "环境配置成功" << std::endl;
        ACTIVATED = "true";
    } else {
        std::cerr << "环境配置失败" <<std::endl;
        run_failed();
    }
}

void install_latex() {
    std::cout << "正在安装 LaTeX 引擎..." << std::endl;
    if (!fs::exists("scripts\\install_latex.bat")) {
        std::cerr << "未找到 LaTeX 安装脚本: scripts\\install_latex.bat" << std::endl;
        run_failed();
    }
    int exit_code = system("scripts\\install_latex.bat");
    if (exit_code == 0) {
        std::cout << "LaTeX 引擎安装成功" << std::endl;
        LATEX_INSTALLED = "true";
    } else {
        std::cerr << "LaTeX 引擎安装失败" << std::endl;
        LATEX_INSTALLED = "false";
        run_failed();
    }
}


void run_project() {
    fs::path root_path = fs::current_path();

    fs::path venv_path = root_path / ".venv";
    fs::path python_exe = venv_path / "Scripts" / "python.exe";
    fs::path script_path = root_path / "src" / "main.py";

    if (!fs::exists(python_exe)) {
        std::cerr << "虚拟环境未就绪，请先运行配置脚本。" << std::endl;
        run_failed();
    }

    std::string command = "set \"PYTHONPATH=" + root_path.string() + "\" && " +
                          "cd /d \"" + (root_path / "src").string() + "\" && " +
                          "\"" + python_exe.string() + "\" main.py";

    int exit_code = system(command.c_str());
    if (exit_code == 0) exit(0);

    std::cerr << "项目运行失败" << std::endl;
    exit_and_wait(1);
}

int main() {
    std::ifstream launcher_json(launcher_json_file_name);
    if (!launcher_json.is_open()) {
        write_to_file();
        launcher_json.close();
        launcher_json.open(launcher_json_file_name);
    }

    json data;
    try {
        launcher_json >> data;
        ACTIVATED = data["activated"];
        LATEX_INSTALLED = data["latex_installed"];
    }catch (const std::exception& e) {
        std::cerr<<"无法解析launcher.json文件"<<std::endl;
        launcher_json.close();
        run_failed();
    }

    if (ACTIVATED=="false") {
        activate();
        write_to_file();
    }
    if (LATEX_INSTALLED == "false") {
        install_latex();
        write_to_file();
    }
    run_project();
    return 0;
}
