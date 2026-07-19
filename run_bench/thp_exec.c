/* thp_exec: clear the inherited PR_SET_THP_DISABLE flag, then exec the
 * given command. Needed because some launchers (e.g. Claude Code) set
 * PR_SET_THP_DISABLE, which children inherit across fork+exec. A process
 * with that flag cannot fault 2MB-aligned /dev/dax mappings (devdax
 * requires PMD huge faults, which vma_thp_disabled() then rejects),
 * so every DAX access dies with SIGBUS "Non-existent physical address".
 * Usage: thp_exec <cmd> [args...]
 */
#include <stdio.h>
#include <unistd.h>
#include <sys/prctl.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <cmd> [args...]\n", argv[0]);
        return 2;
    }
    if (prctl(PR_SET_THP_DISABLE, 0, 0, 0, 0) != 0)
        perror("prctl(PR_SET_THP_DISABLE, 0)");
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 127;
}
