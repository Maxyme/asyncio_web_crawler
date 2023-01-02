CREATE MIGRATION m1meeb447vjzdkvstlnpflshlc66it2r4aytmzyavrpkqdhr7tgmxa
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE ABSTRACT TYPE default::Auditable {
      CREATE REQUIRED PROPERTY created_at -> std::datetime {
          SET default := (std::datetime_current());
          SET readonly := true;
      };
  };
  CREATE SCALAR TYPE default::StatusType EXTENDING enum<in_progress, completed, error>;
  CREATE TYPE default::Job EXTENDING default::Auditable {
      CREATE PROPERTY image_urls -> array<std::str>;
      CREATE PROPERTY input_urls -> array<std::str>;
      CREATE REQUIRED PROPERTY status -> default::StatusType;
      CREATE REQUIRED PROPERTY threads -> std::int16;
  };
};
