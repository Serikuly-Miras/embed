#!/usr/bin/env fish

if test (count $argv) -lt 1
    echo "usage: deploy.fish <project-name>" >&2
    exit 1
end

set PROJECT $argv[1]
set PROJECT_DIR "projects/$PROJECT"
set LIBS_FILE "$PROJECT_DIR/libs.txt"
set LIB_FILES

if not test -d "$PROJECT_DIR"
    echo "No such project: $PROJECT_DIR" >&2
    exit 1
end

if test -f "$LIBS_FILE"
    for name in (cat $LIBS_FILE)
        if test -n "$name"
            set LIB_FILES $LIB_FILES "libs/$name"
        end
    end
end

echo "Stopping running script..."
uv run mpremote exec "pass"
or exit 1

echo "Cleaning board..."
uv run mpremote rm -rf :
or exit 1

echo "Deploying $PROJECT..."
uv run mpremote cp $LIB_FILES $PROJECT_DIR/*.py :
or exit 1

echo "Resetting board..."
uv run mpremote reset

echo "Done. Attaching to console (Ctrl-C to exit)..."
uv run mpremote
