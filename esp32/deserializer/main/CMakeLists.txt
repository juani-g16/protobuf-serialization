idf_component_register(SRCS "main.c" "message.pb-c.c"
                       INCLUDE_DIRS ".")

target_compile_options(${COMPONENT_LIB} PUBLIC -std=gnu23)                       