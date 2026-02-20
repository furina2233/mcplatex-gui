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

void exit_and_wait(const int code) {
    system("pause");
    exit(code);
}

void write_to_file() {
    json data;
    data["activated"] = ACTIVATED;

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
    write_to_file();
    std::cerr<<"请重新启动程序"<<std::endl;
    exit_and_wait(1);
}

void activate() {
    std::cout<<"首次启动，正在配置环境..."<<std::endl;
    if (!fs::exists("sync.bat")) {
        std::cerr << "未找到配置环境脚本" << std::endl;
        run_failed();
    }
    int exit_code = system("sync.bat");
    if (exit_code == 0) {
        std::cout << "环境配置成功" << std::endl;
        ACTIVATED = "true";
    } else {
        std::cerr << "环境配置失败" <<std::endl;
        run_failed();
    }
}

void run_project() {
    // 获取当前工作目录
    fs::path venv_path = fs::current_path() / "src" / ".venv";
    if (!fs::exists(venv_path)) {
        std::cerr << "虚拟环境不存在，请先运行配置脚本" << std::endl;
        run_failed();
    }

    fs::path python_exe = venv_path / "Scripts" / "python.exe";

    if (!fs::exists(python_exe)) {
        std::cerr << "找不到Python解释器: " << python_exe << std::endl;
        run_failed();
    }
    fs::path script_path = fs::current_path() / "src" / "main_with_gui.py";
    if (!fs::exists(script_path)) {
        std::cerr << "找不到主脚本: " << script_path << std::endl;
        run_failed();
    }
    std::string command = "cd /d \"" + (fs::current_path() / "src").string() + "\" && \".venv\\Scripts\\python.exe\" main_with_gui.py";

    int exit_code = system(command.c_str());
    if (exit_code == 0) {
        exit(0);
    }
    std::cerr<<"项目运行失败"<<std::endl;
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
    }catch (const std::exception& e) {
        std::cerr<<"无法解析launcher.json文件"<<std::endl;
        launcher_json.close();
        run_failed();
    }

    if (ACTIVATED=="false") {
        activate();
        write_to_file();
    }
    if (ACTIVATED=="true") {
        run_project();
    }
    return 0;
}
