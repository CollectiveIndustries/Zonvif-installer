    BEGIN { ORS = ""; print " [ "}
    /Network/ {next}
    { printf "%s{\"ip\": \"%s\", \"mac\": \"%s\"}",
          separator, $1, $2
      separator = ", "
    }
    END { print " ] " }

