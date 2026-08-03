#!/usr/bin/env fish

if test (count $argv) -lt 1
    echo "usage: deploy.fish <project-name>" >&2
    exit 1
end

set PROJECT $argv[1]
set PROJECT_DIR "projects/$PROJECT"
set DEPLOY_FILE "$PROJECT_DIR/deploy.toml"
set LIB_FILES
set STATIC_FILES

if not test -d "$PROJECT_DIR"
    echo "No such project: $PROJECT_DIR" >&2
    exit 1
end

if test -f "$DEPLOY_FILE"
    for name in (yq -p toml -oy '.libs // [] | .[]' -r $DEPLOY_FILE)
        if test -n "$name"
            set LIB_FILES $LIB_FILES "libs/$name"
        end
    end

    for name in (yq -p toml -oy '.static // [] | .[]' -r $DEPLOY_FILE)
        if test -n "$name"
            if test -f "static/$name"
                set STATIC_FILES $STATIC_FILES "static/$name"
            else
                echo "Static file not found in repo static/: $name" >&2
                exit 1
            end
        end
    end
end

if test -d "$PROJECT_DIR/static"
    for f in $PROJECT_DIR/static/*
        if test -f "$f"
            set STATIC_FILES $STATIC_FILES "$f"
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

if test (count $STATIC_FILES) -gt 0
    uv run mpremote mkdir :static
    uv run mpremote cp $STATIC_FILES :static/
    or exit 1
end

echo "Resetting board..."
uv run mpremote reset
sleep 1

echo "Done. Attaching to console (Ctrl-C to exit)..."
uv run mpremote
