    BEGIN { ORS = ""; print " [ "}
    /Network/ {next}
    { printf "%s{\"iface\": \"%s\"}",
          separator, $1,
      separator = ", "
    }
    END { print " ] " }
