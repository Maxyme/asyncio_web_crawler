CREATE MIGRATION m123jkqvyvuxefziwhdw4uttfd32gj5uc5ngwb4tw4go54dklnfqaa
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE ABSTRACT TYPE default::Auditable {
      CREATE REQUIRED PROPERTY created_at -> std::datetime {
          SET default := (std::datetime_current());
          SET readonly := true;
      };
  };
  CREATE TYPE default::Job EXTENDING default::Auditable {
      CREATE PROPERTY completed -> std::bool;
      CREATE PROPERTY image_urls -> std::json;
      CREATE PROPERTY in_progress -> std::bool;
      CREATE PROPERTY input_urls -> std::json;
      CREATE PROPERTY threads -> std::int16;
  };
};
