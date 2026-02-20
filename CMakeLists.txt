cmake_minimum_required(VERSION 4.1)
project(launcher)

set(CMAKE_CXX_STANDARD 23)

add_executable(launcher main.cpp
        json.hpp)

if (MINGW)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static")
    target_link_libraries(launcher PRIVATE
            -static-libgcc
            -static-libstdc++
            -pthread
    )
endif()
