    BEGIN { ORS = ""; print " [ "}
    /Network/ {next}
    { printf "%s{\"ip\": \"%s\", \"mac\": \"%s\", \"vendor\": \"%s\", \"onvif\": \"unknown\"}",
          separator, $1, $2, $3
      separator = ", "
    }
    END { print " ] " }

