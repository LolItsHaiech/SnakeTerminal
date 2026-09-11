SNAKE_TYPE_DIR="${0:A:h}"
SNAKE_TYPE_PY="${SNAKE_TYPE_DIR}/game.py"

snake-type-repl() {
  emulate -L zsh
  local key cmd tmpfile

  while true; do
    print -n -- "<Press enter to start typing>"

    if ! read -k1 -s key; then
      print
      return 0
    fi
    print

    if [[ "$key" != $'\n' && "$key" != $'\r' ]]; then
      continue
    fi

    if [[ ! -f "$SNAKE_TYPE_PY" ]]; then
      print -u2 -- "snake-type: cannot find game.py at $SNAKE_TYPE_PY"
      return 1
    fi

    if ! command -v python3 >/dev/null 2>&1; then
      print -u2 -- "snake-type: python3 is required but was not found in PATH"
      return 1
    fi

    tmpfile=$(mktemp "${TMPDIR:-/tmp}/snake-type.XXXXXX") || return 1

    python3 "$SNAKE_TYPE_PY" "$tmpfile" < /dev/tty > /dev/tty

    cmd="$(<"$tmpfile")"
    command rm -f -- "$tmpfile"

    if [[ -z "$cmd" ]]; then
      continue
    fi

    print -- "\$ $cmd"
    eval -- "$cmd"
  done
}

# Autostart on interactive shells only (never in scripts / non-interactive subshells), unless explicitly disabled.
if [[ -o interactive && -z "$SNAKE_TYPE_DISABLE" ]]; then
  snake-type-repl
fi
