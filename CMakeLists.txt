cmake_minimum_required(VERSION 3.22)
project(PixelTunes64)

set(CMAKE_CXX_STANDARD 20)

include(FetchContent)
FetchContent_Declare(
        rpi_rgb_led_matrix
        GIT_REPOSITORY https://github.com/hzeller/rpi-rgb-led-matrix.git
        GIT_TAG master
)
FetchContent_MakeAvailable(rpi_rgb_led_matrix)

# Pfad zur Library
set(LED_MATRIX_DIR ${rpi_rgb_led_matrix_SOURCE_DIR})

# Include-Verzeichnisse
include_directories(${LED_MATRIX_DIR}/include)

add_executable(PixelTunes64 main.cpp)

# Verknüpfe mit der kompilierten Library
target_link_libraries(PixelTunes64
        ${LED_MATRIX_DIR}/lib/librgbmatrix.a
        pthread
)

add_custom_command(
        OUTPUT ${LED_MATRIX_DIR}/lib/librgbmatrix.a
        COMMAND make -C ${LED_MATRIX_DIR}/lib
        WORKING_DIRECTORY ${LED_MATRIX_DIR}
        COMMENT "Kompiliere RGB Matrix Library"
)
add_custom_target(rgb_matrix_lib DEPENDS ${LED_MATRIX_DIR}/lib/librgbmatrix.a)
add_dependencies(PixelTunes64 rgb_matrix_lib)